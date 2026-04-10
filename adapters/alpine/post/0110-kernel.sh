chroot_rootfs apk add mkinitfs
for module in $ROOTFS/lib/modules/*; do
    kernel_version=$(basename "$module")
    cp -r "$ROOTFS/lib/modules/$kernel_version/dtb" "$ROOTFS/boot/dtb"
    cp -r "$ROOTFS/lib/modules/$kernel_version/vmlinuz" "$ROOTFS/boot/vmlinuz-$kernel_version"
    chroot_rootfs mkinitfs -o "/boot/initramfs-$kernel_version" "$kernel_version"
done
chroot_rootfs update-grub