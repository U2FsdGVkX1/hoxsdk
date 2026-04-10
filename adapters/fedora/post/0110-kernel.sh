echo 'hostonly="no"' > $ROOTFS/etc/dracut.conf.d/no-hostonly.conf
chroot_rootfs kernel-install add-all
rm -rf $ROOTFS/etc/dracut.conf.d/no-hostonly.conf