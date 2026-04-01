for module in $ROOTFS/lib/modules/*; do
    kernel_version=$(basename "$module")
    chroot_rootfs mkinitfs "$kernel_version"
done