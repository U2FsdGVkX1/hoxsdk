import asyncio
import math
import os
import shutil
from dataclasses import dataclass
from graphlib import CycleError, TopologicalSorter
from pathlib import Path
from shlex import quote

from dotenv import dotenv_values

from hox import Board, ImagePartition, Module
from process import command_log, shell


@dataclass(frozen=True)
class DebugConfig:
    module_name: str
    action_index: str

    def matches(self, module_name: str, action_index: int) -> bool:
        return (self.module_name in ("*", module_name)) and (
            self.action_index in ("*", str(action_index))
        )


class Manager:
    SECTOR_SIZE = 512
    GPT_BACKUP_SECTORS = 33

    def __init__(
        self,
        config: Board,
        boarddir: Path,
        adapterdir: Path,
        builddir: Path,
        outputdir: Path,
        logdir: Path,
        debug: list[DebugConfig] | None = None,
        params: dict[str, str] | None = None,
    ):
        self.config = config
        self.boarddir = boarddir.resolve()
        self.adapterdir = adapterdir.resolve()
        self.builddir = builddir.resolve()
        self.outputdir = outputdir.resolve()
        self.logdir = logdir.resolve()
        self.debug = tuple(debug or [])
        self.params = dict(params or {})

    @staticmethod
    def _dependencies(modules: list[Module], stage: str) -> dict[str, set[str]]:
        module_names = { module.name for module in modules }
        depends_map: dict[str, set[str]] = { module.name: set() for module in modules }
        for module in modules:
            for dependency in getattr(module, f"{stage}_after"):
                if dependency in module_names:
                    depends_map[module.name].add(dependency)
            for target in getattr(module, f"{stage}_before"):
                if target in module_names:
                    depends_map[target].add(module.name)

        try:
            TopologicalSorter(depends_map).prepare()
        except CycleError as exc:
            raise ValueError(f"Circular dependency detected among modules: {exc}") from exc
        return depends_map

    @staticmethod
    def _dependency_order(modules: list[Module], stage: str) -> list[Module]:
        module_map = { module.name: module for module in modules }
        depends_map = Manager._dependencies(modules, stage)
        return [module_map[name] for name in TopologicalSorter(depends_map).static_order()]

    @staticmethod
    def _partition_size(image_partition: ImagePartition, workdir: Path) -> int:
        if image_partition.size:
            return image_partition.size

        partition_image = (workdir / image_partition.name).resolve()
        if not partition_image.is_file():
            raise FileNotFoundError(f"Partition image not found: {partition_image}")

        size = partition_image.stat().st_size
        return math.ceil(size / Manager.SECTOR_SIZE)

    async def build(self) -> None:
        async def run_build(module: Module) -> None:
            moduledir = self.builddir / module.name
            if moduledir.exists():
                shutil.rmtree(moduledir)
            moduledir.mkdir(parents=True, exist_ok=True)

            with command_log(self.logdir / f"{module.name}.log"):
                for index, action in enumerate(module.build):
                    env = {**module.env, **dotenv_values(moduledir / ".env")}
                    if any(item.matches(module.name, index) for item in self.debug):
                        print(f"[debug] Paused before {module.name}:{index} ({action.use})")
                        print(f"[debug] cwd: {moduledir}")
                        print("[debug] Exit the shell to continue")
                        process = await asyncio.create_subprocess_exec(
                            os.environ.get("SHELL") or "/bin/bash",
                            cwd=moduledir,
                            env=os.environ | env,
                        )
                        await process.wait()
                    await action.run(moduledir, env)
        modules = [module for module in self.config.modules if module.build]
        if self.debug:
            for module in self._dependency_order(modules, "build"):
                await run_build(module)
            return

        depends_map = self._dependencies(modules, "build")
        finished = { module.name: asyncio.Event() for module in modules }
        async def run_when_ready(module: Module) -> None:
            for dependency in depends_map[module.name]:
                await finished[dependency].wait()
            await run_build(module)
            finished[module.name].set()

        async with asyncio.TaskGroup() as group:
            for module in modules:
                group.create_task(run_when_ready(module))

    async def _write_images(self, workdir: Path) -> None:
        for image in self.config.images:
            disk = (self.outputdir / image.name).resolve()

            sfdisk_lines = [f"label: {image.table}", "unit: sectors", ""]
            total_sectors = 0
            for image_partition in image.partitions:
                size = self._partition_size(image_partition, workdir)
                total_sectors = max(total_sectors, image_partition.start + size)
                fields = [f"start={image_partition.start}", f"size={size}"]

                if image_partition.type is not None:
                    fields.append(f"type={image_partition.type}")

                if image_partition.bootable:
                    fields.append("bootable")

                sfdisk_lines.append(", ".join(fields))
            if image.table == "gpt":
                total_sectors += self.GPT_BACKUP_SECTORS

            sfdisk_script = workdir / f"{disk.name}.sfdisk"
            sfdisk_script.write_text("\n".join(sfdisk_lines) + "\n")
            with disk.open("wb") as file:
                file.truncate(total_sectors * self.SECTOR_SIZE)
            await shell(
                f"sfdisk --wipe always --wipe-partitions always "
                f"{quote(str(disk))} < {quote(str(sfdisk_script))}"
            )

            for image_partition in image.partitions:
                partition_image = (workdir / image_partition.name).resolve()
                capacity = self._partition_size(image_partition, workdir) * self.SECTOR_SIZE
                image_size = partition_image.stat().st_size
                if image_size > capacity:
                    raise ValueError(
                        f"Partition image {partition_image} is larger than configured size "
                        f"({image_size} > {capacity})"
                    )
                await shell(
                    f"dd if={quote(str(partition_image))} of={quote(str(disk))} "
                    f"bs={self.SECTOR_SIZE} seek={image_partition.start} "
                    "conv=notrunc,sparse status=none"
                )

    async def images(self) -> None:
        with command_log(self.logdir / "_image.log"):
            for tool in ("sfdisk", "dd"):
                if not shutil.which(tool):
                    raise RuntimeError(f"Required tool '{tool}' not found in PATH")

            workdir = (self.builddir / "_image").resolve()
            rootfs = (workdir / "rootfs").resolve()
            rootfs.mkdir(parents=True, exist_ok=True)
            env = {
                "ROOTFS": str(rootfs),
                "BOARD_NAME": self.boarddir.name,
                "BOARD_DIR": str(self.boarddir),
                "ADAPTER_NAME": self.adapterdir.name,
                "ADAPTER_DIR": str(self.adapterdir),
                "BUILD_DIR": str(self.builddir),
                "OUTPUT_DIR": str(self.outputdir),
                "ARCH": self.config.arch,
                **self.params,
            }

            mounted: dict[Path, Path] = {}
            for partition in self.config.partitions:
                partition_image = (workdir / partition.name).resolve()
                partition_mountpoint = (
                    rootfs / partition.mountpoint.lstrip("/")
                ).resolve()

                with partition_image.open("wb") as file:
                    file.truncate(partition.size * self.SECTOR_SIZE)
                await shell(f"{partition.mkfs} {quote(str(partition_image))}")
                mounted[partition_image] = partition_mountpoint

            try:
                for partition_image, partition_mountpoint in mounted.items():
                    assert str(partition_mountpoint) != "/"
                    await shell(f"sudo -E rm -rf {quote(str(partition_mountpoint))}")
                    await shell(f"sudo -E mkdir -p {quote(str(partition_mountpoint))}")
                    await shell(
                        f"sudo -E mount -o loop "
                        f"{quote(str(partition_image))} "
                        f"{quote(str(partition_mountpoint))}"
                    )

                scripts = ["set -euo pipefail"]
                modules = [module for module in self.config.modules if module.install]
                for module in self._dependency_order(modules, "install"):
                    scripts.append(
                        f"export MODULE_DIR={quote(str(self.builddir / module.name))}"
                    )
                    for item in module.install:
                        if isinstance(item, Path):
                            scripts.append(f"source {quote(str(item))}")
                        else:
                            scripts.append(item)

                scripts_path = workdir / "install.sh"
                scripts_path.write_text("\n".join(scripts))
                await shell(
                    f"sudo -E bash {quote(str(scripts_path))}", cwd=rootfs, env=env
                )
            finally:
                await shell(
                    f"grep {quote(str(rootfs))} /proc/mounts | "
                    "cut -d' ' -f2 | sort -r | xargs -r sudo -E umount"
                )
            await self._write_images(workdir)
