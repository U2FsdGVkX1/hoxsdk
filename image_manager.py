import shutil
from pathlib import Path
from shlex import quote

from sdkhelper import shell


class ImageManager:
    def __init__(
        self,
        arch: str,
        desktop: str,
        partitions: list[dict],
        boarddir: Path,
        adapterdir: Path,
        builddir: Path,
        outputdir: Path,
    ):
        if not shutil.which("genimage"):
            raise EnvironmentError("Required tool 'genimage' not found in PATH")

        self.arch = arch
        self.desktop = desktop
        self.partitions = partitions
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

    async def _load_partitions(self, workdir: Path, rootfs: Path) -> list[tuple[Path, Path]]:
        partitions = []
        for partition in self.partitions:
            name = partition["name"]
            mountpoint = partition["mountpoint"]
            size = partition["size"]
            mkfs_cmd = partition["mkfs"]

            image = workdir / f"{name}.img"
            mountdir = rootfs if mountpoint == "/" else rootfs / mountpoint.lstrip("/")
            await shell(f"truncate -s {quote(size)} {quote(str(image))}")
            await shell(f"{mkfs_cmd} {quote(str(image))}")
            partitions.append((image, mountdir))
        return partitions

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
            f"bash -lc {quote('\n'.join(cmds))}",
            cwd=rootfs,
            env=env
        )

    async def generate(self):
        workdir = (self.builddir / "_image").resolve()
        if workdir.exists():
            shutil.rmtree(workdir)
        rootfs = (workdir / "rootfs").resolve()
        rootfs.mkdir(parents=True, exist_ok=True)

        env = self._build_env(rootfs)
        partitions = await self._load_partitions(workdir, rootfs)
        try:
            for image, mountpoint in partitions:
                mountpoint.mkdir(parents=True, exist_ok=True)
                await shell(
                    f"mount -o loop {quote(str(image))} {quote(str(mountpoint))}"
                )
            await self._source_scripts(rootfs, env)
        finally:
            await shell(f"grep {quote(str(rootfs))} /proc/mounts | cut -d' ' -f2 | sort -r | xargs -r umount")
        
        genimage_cfg = self.boarddir / "genimage.cfg"
        await shell(
            f"genimage "
            f"--config {quote(str(genimage_cfg))} "
            f"--inputpath {quote(str(workdir))} "
            f"--outputpath {quote(str(self.outputdir))}",
        )
