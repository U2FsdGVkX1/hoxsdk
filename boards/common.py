from types import SimpleNamespace

from actions import git, make
from hox import (
    Image,
    ImagePartition,
    Module,
    Partition,
)


SECTOR = 512
KiB = 1024 // SECTOR
MiB = 1024 * KiB
GiB = 1024 * MiB

EFI_SIZE: int = 500 * MiB
BOOT_SIZE: int = 1 * GiB
ROOTFS_SIZE: int = 15 * GiB

KERNEL_INSTALL = """\
kernel_version=$(basename "$MODULE_DIR/modules/lib/modules/"*)
cp -r "$MODULE_DIR/modules/lib/modules/$kernel_version" "$ROOTFS/lib/modules/$kernel_version"
cp -r "$MODULE_DIR/dtb" "$ROOTFS/lib/modules/$kernel_version/dtb"
cp -r "$MODULE_DIR"/arch/*/boot/Image.gz "$ROOTFS/lib/modules/$kernel_version/vmlinuz"
"""


def default_partitions():
    return [
        Partition(name="rootfs.img", size=ROOTFS_SIZE, mkfs="mkfs.ext4", mountpoint="/"),
        Partition(name="boot.img", size=BOOT_SIZE, mkfs="mkfs.ext4", mountpoint="/boot"),
        Partition(name="efi.img", size=EFI_SIZE, mkfs="mkfs.fat -F 32", mountpoint="/boot/efi"),
    ]


def default_images():
    return [
        Image(
            name="sdcard.img",
            partitions=[
                ImagePartition(
                    name="efi.img",
                    start=1 * MiB,
                    type="C12A7328-F81F-11D2-BA4B-00A0C93EC93B",
                ),
                ImagePartition(
                    name="boot.img",
                    start=1 * MiB + EFI_SIZE,
                    type="BC13C2FF-59E6-4262-A352-B275FD6F7172",
                ),
                ImagePartition(
                    name="rootfs.img",
                    start=1 * MiB + EFI_SIZE + BOOT_SIZE,
                    type="0FC63DAF-8483-4772-8E79-3D69D8477DE4",
                ),
            ],
        )
    ]


def firmware(arch: str):
    cross = {
        "x86_64": "x86_64-linux-gnu-",
        "riscv64": "riscv64-linux-gnu-",
        "aarch64": "aarch64-linux-gnu-",
    }[arch]
    arch_flag = {
        "x86_64": {"opensbi": "x86_64", "uboot": "x86", "kernel": "x86_64"},
        "riscv64": {"opensbi": "riscv", "uboot": "riscv", "kernel": "riscv"},
        "aarch64": {"opensbi": "arm64", "uboot": "arm64", "kernel": "arm64"},
    }[arch]
    gcc = cross + "gcc"

    def opensbi(
        src,
        args="PLATFORM=generic",
        prebuild=(),
        postbuild=(),
        install=(),
        build_after=(),
        build_before=(),
        install_after=(),
        install_before=(),
    ):
        return Module(
            name="opensbi",
            build=[git(src=src), *prebuild, make(args=args), *postbuild],
            install=install,
            build_after=build_after,
            build_before=build_before,
            install_after=install_after,
            install_before=install_before,
            requires=["git", "patch", "make", gcc],
            env={"CROSS_COMPILE": cross, "ARCH": arch_flag["opensbi"]},
        )

    def uboot(
        src,
        defconfig,
        args="",
        prebuild=(),
        postbuild=(),
        install=(),
        build_after=(),
        build_before=(),
        install_after=(),
        install_before=(),
    ):
        return Module(
            name="uboot",
            build=[
                git(src=src),
                *prebuild,
                make(args=defconfig),
                make(args=args),
                *postbuild,
            ],
            install=install,
            build_after=build_after,
            build_before=build_before,
            install_after=install_after,
            install_before=install_before,
            requires=["git", "patch", "make", gcc],
            env={"CROSS_COMPILE": cross, "ARCH": arch_flag["uboot"]},
        )

    def kernel(
        src,
        defconfig,
        args="",
        prebuild=(),
        postbuild=(),
        install=(KERNEL_INSTALL,),
        build_after=(),
        build_before=(),
        install_after=("image-rootfs",),
        install_before=("image-kernel",),
    ):
        return Module(
            name="kernel",
            build=[
                git(src=src),
                *prebuild,
                make(args=defconfig),
                make(args=args),
                make(args="INSTALL_MOD_PATH=modules DEPMOD=true modules_install"),
                make(args="INSTALL_DTBS_PATH=dtb dtbs_install"),
                *postbuild,
            ],
            install=install,
            build_after=build_after,
            build_before=build_before,
            install_after=install_after,
            install_before=install_before,
            requires=["git", "patch", "make", gcc],
            env={
                "CROSS_COMPILE": cross,
                "ARCH": arch_flag["kernel"],
                "INSTALL_MOD_STRIP": "1",
                "XZ_DEFAULTS": "--check=crc32",
            },
        )

    return SimpleNamespace(opensbi=opensbi, uboot=uboot, kernel=kernel)
