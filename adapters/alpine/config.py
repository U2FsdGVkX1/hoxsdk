from hox import ConfigContext, Module


def configure(ctx: ConfigContext) -> list[Module]:
    return [
        Module(name="image-common", install=[ctx.ADAPTER_DIR / "000-common.sh"]),
        Module(
            name="image-rootfs",
            install_after=["image-common"],
            install=[ctx.ADAPTER_DIR / "010-rootfs.sh"],
        ),
        Module(
            name="image-grub",
            install_after=["image-rootfs"],
            install=[ctx.ADAPTER_DIR / "110-grub.sh"],
        ),
        Module(
            name="image-kernel",
            install_after=["image-grub"],
            install=[ctx.ADAPTER_DIR / "120-kernel.sh"],
        ),
        Module(
            name="image-fstab",
            install_after=["image-kernel"],
            install=[ctx.ADAPTER_DIR / "130-fstab.sh"],
        ),
        Module(
            name="image-final",
            install_after=["image-fstab"],
            install=[ctx.ADAPTER_DIR / "200-final.sh"],
        ),
    ]
