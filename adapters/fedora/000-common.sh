chroot_rootfs() {
    # Bind essential system directories for chroot environment
    mount --bind /etc/resolv.conf "$ROOTFS/etc/resolv.conf"
    mount --bind /etc/hosts "$ROOTFS/etc/hosts"
    mount -t proc none "$ROOTFS/proc"
    mount -t sysfs none "$ROOTFS/sys"
    mount -t devtmpfs none "$ROOTFS/dev"
    
    # Execute command in chroot
    chroot "$ROOTFS" sh -c "$*"
    
    # Clean up mounted directories
    umount -l "$ROOTFS/dev" "$ROOTFS/sys" "$ROOTFS/proc" "$ROOTFS/etc/resolv.conf" "$ROOTFS/etc/hosts"
}
