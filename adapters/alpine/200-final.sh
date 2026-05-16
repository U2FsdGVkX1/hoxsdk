chroot_rootfs "echo 'root:hoxsdk' | chpasswd"
chroot_rootfs "rc-update add localmount boot"
chroot_rootfs "rc-update add mount-ro shutdown"
