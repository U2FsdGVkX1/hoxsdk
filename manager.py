import asyncio
import math
import os
import shutil
from contextlib import nullcontext
from fnmatch import fnmatchcase
from graphlib import TopologicalSorter
from pathlib import Path
from shlex import quote

from dotenv import dotenv_values

from hox import Board, Module
from process import command_log, shell


class Manager:
    SECTOR_SIZE = 512
    ALIGNMENT = 2048
    GPT_BACKUP_SECTORS = 33

    def __init__(
        self,
        config: Board,
        boarddir: Path,
        adapterdir: Path,
        builddir: Path,
        outputdir: Path,
        logdir: Path,
        debug: list[str] | None = None,
        params: dict[str, str] | None = None,
    ):
        self.config = config
        self.boarddir = boarddir
        self.adapterdir = adapterdir
        self.builddir = builddir
        self.outputdir = outputdir
        self.logdir = logdir
        self.debug = tuple(debug or [])
        self.params = dict(params or {})

    def _dependencies(self, stage: str) -> dict[str, set[str]]:
        depends_map = {
            module.name: set(getattr(module, f"{stage}_after"))
            for module in self.config.modules
        }
        for module in self.config.modules:
            for target in getattr(module, f"{stage}_before"):
                depends_map[target].add(module.name)
        TopologicalSorter(depends_map).prepare()
        return depends_map

    def _dependency_order(self, stage: str) -> list[Module]:
        module_map = { module.name: module for module in self.config.modules }
        order = TopologicalSorter(self._dependencies(stage)).static_order()
        return [module_map[name] for name in order]

    async def build(self) -> None:
        async def run_build(module: Module) -> None:
            moduledir = self.builddir / module.name
            if moduledir.exists():
                shutil.rmtree(moduledir)
            moduledir.mkdir(parents=True, exist_ok=True)

            with command_log(self.logdir / f"{module.name}.log"):
                for index, action in enumerate(module.build):
                    env = {**module.env, **dotenv_values(moduledir / ".env")}
                    if any(fnmatchcase(f"{module.name}:{index}", pattern) for pattern in self.debug):
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

        depends_map = self._dependencies("build")
        finished = { name: asyncio.Event() for name in depends_map }
        serial = asyncio.Lock() if self.debug else nullcontext()
        async def run_when_ready(module: Module) -> None:
            for dependency in depends_map[module.name]:
                await finished[dependency].wait()
            if module.build:
                async with serial:
                    await run_build(module)
            finished[module.name].set()

        async with asyncio.TaskGroup() as group:
            for module in self.config.modules:
                group.create_task(run_when_ready(module))

    async def _write_images(self, workdir: Path) -> None:
        for image in self.config.images:
            disk = self.outputdir / image.name
            sfdisk_lines = [f"label: {image.table}", "unit: sectors", ""]

            layout: list[tuple[Path, int]] = []
            end = self.ALIGNMENT
            for image_partition in image.partitions:
                partition_image = workdir / image_partition.name
                used = math.ceil(partition_image.stat().st_size / self.SECTOR_SIZE)
                size = image_partition.size or used
                if used > size:
                    raise ValueError(
                        f"Partition image {partition_image} is larger than configured size "
                        f"({used} > {size} sectors)"
                    )
                start = image_partition.start
                if start is None:
                    start = math.ceil(end / self.ALIGNMENT) * self.ALIGNMENT
                end = max(end, start + size)
                layout.append((partition_image, start))
                sfdisk_lines.append(", ".join(filter(None, [
                    f"start={start}",
                    f"size={size}",
                    f"type={image_partition.type}" if image_partition.type else None,
                    "bootable" if image_partition.bootable else None,
                ])))
            if image.table == "gpt":
                end += self.GPT_BACKUP_SECTORS

            sfdisk_script = workdir / f"{image.name}.sfdisk"
            sfdisk_script.write_text("\n".join(sfdisk_lines) + "\n")
            with disk.open("wb") as file:
                file.truncate(end * self.SECTOR_SIZE)
            await shell(f"sfdisk {quote(str(disk))} < {quote(str(sfdisk_script))}")
            for partition_image, start in layout:
                await shell(
                    f"dd if={quote(str(partition_image))} of={quote(str(disk))} "
                    f"bs={self.SECTOR_SIZE} seek={start} conv=notrunc,sparse status=none"
                )

    async def images(self) -> None:
        with command_log(self.logdir / "_image.log"):
            for tool in ("sfdisk", "dd"):
                if not shutil.which(tool):
                    raise RuntimeError(f"Required tool '{tool}' not found in PATH")

            workdir = self.builddir / "_image"
            # Install scripts compare $ROOTFS with findmnt output, so it must be a real path.
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

            try:
                for partition in self.config.partitions:
                    partition_image = workdir / partition.name
                    partition_mountpoint = rootfs / partition.mountpoint.lstrip("/")
                    with partition_image.open("wb") as file:
                        file.truncate(partition.size * self.SECTOR_SIZE)
                    await shell(f"{partition.mkfs} {quote(str(partition_image))}")
                    await shell(f"sudo mkdir -p {quote(str(partition_mountpoint))}")
                    await shell(
                        f"sudo mount -o loop {quote(str(partition_image))} "
                        f"{quote(str(partition_mountpoint))}"
                    )

                scripts = ["set -euo pipefail"]
                for module in self._dependency_order("install"):
                    if not module.install:
                        continue
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
                if rootfs.is_mount():
                    await shell(f"sudo umount -R {quote(str(rootfs))}")
            await self._write_images(workdir)
