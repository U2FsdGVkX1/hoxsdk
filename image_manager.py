import shutil
from pathlib import Path
from shlex import quote
from typing import Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    RootModel,
    field_validator,
    model_validator,
)

from process import shell


class Partition(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str
    size: int = Field(gt=0)
    mountpoint: str = Field(min_length=1)
    mkfs: str = Field(min_length=1)


class ImagePartition(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str
    start: int = Field(ge=0)
    size: int | None = Field(default=None, gt=0)
    type: str | None = None
    bootable: bool = False


class Image(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str
    table: Literal["gpt", "dos"] = "gpt"
    partitions: tuple[ImagePartition, ...]

    @field_validator("table", mode="before")
    @classmethod
    def normalize_table(cls, table: Any) -> Any:
        if table in ("mbr", "msdos"):
            return "dos"
        return table


class PartitionList(RootModel[tuple[Partition, ...]]):
    model_config = ConfigDict(frozen=True)

    @model_validator(mode="after")
    def validate_names(self) -> "PartitionList":
        names = [partition.name for partition in self.root]
        if len(names) != len(set(names)):
            raise ValueError("Partition names must be unique")

        mountpoints = [str(partition.mountpoint) for partition in self.root]
        if len(mountpoints) != len(set(mountpoints)):
            raise ValueError("Partition mountpoints must be unique")
        return self


class ImageList(RootModel[tuple[Image, ...]]):
    model_config = ConfigDict(frozen=True)

    @model_validator(mode="after")
    def validate_names(self) -> "ImageList":
        names = [image.name for image in self.root]
        if len(names) != len(set(names)):
            raise ValueError("Image names must be unique")
        return self


class ImageManager:
    SECTOR_SIZE = 512
    GPT_BACKUP_SECTORS = 33

    def __init__(
        self,
        arch: str,
        desktop: str,
        partitions: list[dict[str, Any]],
        images: list[dict[str, Any]],
        boarddir: Path,
        adapterdir: Path,
        builddir: Path,
        outputdir: Path,
    ):
        for tool in ("sfdisk", "dd"):
            if not shutil.which(tool):
                raise EnvironmentError(f"Required tool '{tool}' not found in PATH")

        self.arch = arch
        self.desktop = desktop
        self.partitions = PartitionList.model_validate(partitions).root
        self.images = ImageList.model_validate(images).root
        self.boarddir = boarddir.resolve()
        self.adapterdir = adapterdir.resolve()
        self.builddir = builddir.resolve()
        self.outputdir = outputdir.resolve()

    def _build_env(self, rootfs: Path) -> dict[str, str]:
        return {
            "ROOTFS": str(rootfs),
            "BOARD_NAME": self.boarddir.name,
            "BOARD_DIR": str(self.boarddir),
            "ADAPTER_NAME": self.adapterdir.name,
            "ADAPTER_DIR": str(self.adapterdir),
            "BUILD_DIR": str(self.builddir),
            "OUTPUT_DIR": str(self.outputdir),
            "FIRMWARE_DIR": str(self.outputdir),
            "ARCH": self.arch,
            "DESKTOP": self.desktop,
        }

    def _partition_size(self, image_partition: ImagePartition, workdir: Path) -> int:
        if image_partition.size:
            return image_partition.size

        partition_image = (workdir / image_partition.name).resolve()
        if not partition_image.is_file():
            raise FileNotFoundError(f"Partition image not found: {partition_image}")

        size = partition_image.stat().st_size
        return (size + self.SECTOR_SIZE - 1) // self.SECTOR_SIZE

    async def _source_scripts(self, rootfs: Path, env: dict[str, str]) -> None:
        cmds = ["set -euo pipefail"]
        for stage in ("pre", "post"):
            scripts: list[Path] = []
            for sourcedir in (self.adapterdir / stage, self.boarddir / stage):
                if not sourcedir.is_dir():
                    continue
                for script in sourcedir.glob("*.sh"):
                    scripts.append(script.resolve())
            for script in sorted(scripts, key=lambda p: p.name):
                cmds.append(f"source {quote(str(script))}")
        await shell(
            f"sudo -E bash -lc {quote('\n'.join(cmds))}",
            cwd=rootfs,
            env=env,
        )

    async def _write_images(self, workdir: Path) -> None:
        for image in self.images:
            disk = (self.outputdir / image.name).resolve()

            sfdisk_lines = [f"label: {image.table}", "unit: sectors", ""]
            total_sectors = 0
            for image_partition in image.partitions:
                size = self._partition_size(image_partition, workdir)
                # Partition order defines numbering, not necessarily physical order.
                total_sectors = max(total_sectors, image_partition.start + size)
                fields = [
                    f"start={image_partition.start}",
                    f"size={size}",
                ]
                if image_partition.type is not None:
                    fields.append(f"type={image_partition.type}")
                if image_partition.bootable:
                    fields.append("bootable")
                sfdisk_lines.append(", ".join(fields))
            if image.table == "gpt":
                total_sectors += self.GPT_BACKUP_SECTORS

            sfdisk_script = workdir / f"{disk.name}.sfdisk"
            sfdisk_script.write_text("\n".join(sfdisk_lines) + "\n")
            with disk.open("wb") as f:
                f.truncate(total_sectors * self.SECTOR_SIZE)
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

    async def generate(self):
        workdir = (self.builddir / "_image").resolve()
        rootfs = (workdir / "rootfs").resolve()
        rootfs.mkdir(parents=True, exist_ok=True)

        env = self._build_env(rootfs)
        mounted: dict[Path, Path] = {}
        for partition in self.partitions:
            partition_image = (workdir / partition.name).resolve()
            partition_mountpoint = (rootfs / partition.mountpoint.lstrip("/")).resolve()

            with partition_image.open("wb") as f:
                f.truncate(partition.size * self.SECTOR_SIZE)
            await shell(f"{partition.mkfs} {quote(str(partition_image))}")
            mounted[partition_image] = partition_mountpoint

        try:
            for partition_image, partition_mountpoint in sorted(
                mounted.items(),
                key=lambda item: len(item[1].relative_to(rootfs).parts),
            ):
                await shell(f"sudo -E rm -rf {quote(str(partition_mountpoint))}")
                await shell(f"sudo -E mkdir -p {quote(str(partition_mountpoint))}")
                await shell(
                    f"sudo -E mount -o loop "
                    f"{quote(str(partition_image))} "
                    f"{quote(str(partition_mountpoint))}"
                )
            await self._source_scripts(rootfs, env)
        finally:
            await shell(
                f"grep {quote(str(rootfs))} /proc/mounts | "
                "cut -d' ' -f2 | sort -r | xargs -r sudo -E umount"
            )
        await self._write_images(workdir)
