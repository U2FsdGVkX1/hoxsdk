from boards.common import default_images, default_partitions, firmware
from hox import Board, ConfigContext, Module


def configure(ctx: ConfigContext) -> Board:
    arch = "riscv64"
    fw = firmware(arch)
    modules = ctx.adapter + [
        fw.opensbi("https://github.com/riscv-software-src/opensbi"),
        fw.uboot("https://github.com/u-boot/u-boot", "qemu-riscv64_smode_defconfig"),
        fw.kernel("https://github.com/torvalds/linux", "defconfig"),
    ]
    if ctx.ADAPTER_NAME == "alpine":
        modules.append(Module(
            name="qemu-console",
            install_after=["image-rootfs"],
            install=[
                'echo "ttyS0::respawn:/sbin/getty -L 115200 ttyS0 vt100" >> "$ROOTFS/etc/inittab"'
            ],
        ))

    return Board(
        arch=arch,
        partitions=default_partitions(),
        images=default_images(),
        modules=modules,
    )
