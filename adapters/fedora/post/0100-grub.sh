case "$ARCH" in
    x86_64|amd64)
        grub_packages="shim-x64 grub2-efi-x64"
        ;;
    aarch64|arm64)
        grub_packages="shim-aa64 grub2-efi-aa64"
        ;;
    riscv64)
        grub_packages="shim-unsigned-riscv64 grub2-efi-riscv64"
        ;;
esac

chroot_rootfs dnf install -y $grub_packages
rm -rf $ROOTFS/etc/grub.d/30_os-prober
chroot_rootfs grub2-mkconfig -o /boot/grub2/grub.cfg