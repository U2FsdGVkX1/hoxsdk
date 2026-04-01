while read -r uuid mountpoint fstype; do
    mountpoint_r="${mountpoint#$ROOTFS}"  # Remove ROOTFS prefix
    if [ -z "$mountpoint_r" ]; then
        mountpoint_r="/"
    fi
    echo -e "UUID=${uuid}\t${mountpoint_r}\t${fstype}\tdefaults\t0 0" >> "$ROOTFS/etc/fstab"
done < <(findmnt -Rln -o UUID,TARGET,FSTYPE "$ROOTFS")