case "${ARCH}" in
    x86_64|amd64)
        alpine_arch="x86_64"
        grub_target="x86_64-efi"
        ;;
    aarch64|arm64)
        alpine_arch="aarch64"
        grub_target="arm64-efi"
        ;;
    riscv64)
        alpine_arch="riscv64"
        grub_target="riscv64-efi"
        ;;
    *)
        echo "Unsupported Alpine arch: ${ARCH}" >&2
        return 1
        ;;
esac

chroot_rootfs grub-install --modules="part_gpt" --target=${grub_target} \
                           --efi-directory=/boot/efi --removable
chroot_rootfs update-grub