while read -r uuid mountpoint fstype; do
    mountpoint_r="${mountpoint#$ROOTFS}"  # Remove ROOTFS prefix
    if [ -z "$mountpoint_r" ]; then
        mountpoint_r="/"
    fi
    printf 'UUID=%s\t%s\t%s\tdefaults\t0 0\n' "$uuid" "$mountpoint_r" "$fstype" >> "$ROOTFS/etc/fstab"
done < <(findmnt -Rln -o UUID,TARGET,FSTYPE "$ROOTFS")