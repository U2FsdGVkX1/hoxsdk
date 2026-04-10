kernel_version=$(basename "$FIRMWARE_DIR/modules/lib/modules/"*)
cp -r "$FIRMWARE_DIR/modules/lib/modules/$kernel_version" "$ROOTFS/lib/modules/$kernel_version"
cp -r "$FIRMWARE_DIR/dtb" "$ROOTFS/lib/modules/$kernel_version/dtb"
cp -r "$FIRMWARE_DIR/Image.gz" "$ROOTFS/lib/modules/$kernel_version/vmlinuz"