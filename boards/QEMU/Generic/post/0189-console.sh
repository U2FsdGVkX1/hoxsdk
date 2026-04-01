if [ "$ADAPTER_NAME" = "alpine" ]; then
    echo "ttyS0::respawn:/sbin/getty -L 115200 ttyS0 vt100" >> "$ROOTFS/etc/inittab"
fi