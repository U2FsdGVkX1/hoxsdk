if [ "$ADAPTER_NAME" = "alpine" ]; then
    cp $FIRMWARE_DIR/Image.gz $ROOTFS/boot/vmlinuz-qemu
    cp -r $FIRMWARE_DIR/dtbs $ROOTFS/boot/dtb
    kernel_version=$(ls $FIRMWARE_DIR/modules/lib/modules/ | head -n 1)
    cp -r $FIRMWARE_DIR/modules/lib/modules/$kernel_version "$ROOTFS/lib/modules/${kernel_version}-qemu"
fi