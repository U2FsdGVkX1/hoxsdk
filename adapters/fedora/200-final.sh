chroot_rootfs "echo 'root:hoxsdk' | chpasswd"
chroot_rootfs systemctl enable systemd-timesyncd
chroot_rootfs dnf clean all

while read -r mountpoint fstype; do
    mountpoint_r="${mountpoint#$ROOTFS}"  # Remove ROOTFS prefix
    if [ -z "$mountpoint_r" ]; then
        mountpoint_r="/"
    fi

    if [ $fstype != "vfat" ]; then
        # Do not mount the virtual file system
        chroot "$ROOTFS" bash -c "setfiles /etc/selinux/targeted/contexts/files/file_contexts $mountpoint_r"
    fi
done < <(findmnt -Rln -o TARGET,FSTYPE "$ROOTFS" | tac)
