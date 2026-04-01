case "$ARCH" in
    x86_64|amd64)
        alpine_arch="x86_64"
        ;;
    aarch64|arm64)
        alpine_arch="aarch64"
        ;;
    riscv64)
        alpine_arch="riscv64"
        ;;
    *)
        echo "Unsupported Alpine arch: $ARCH" >&2
        return 1
        ;;
esac

rootfs_url="https://dl-cdn.alpinelinux.org/alpine/v3.23/releases/${alpine_arch}/alpine-minirootfs-3.23.3-${alpine_arch}.tar.gz"
curl -L "$rootfs_url" -o "alpine.tar.gz"
tar -xzf "alpine.tar.gz" -C "$ROOTFS"
rm "alpine.tar.gz"

# Patch: alpine don't have the files
touch "$ROOTFS/etc/resolv.conf"
mkdir "$ROOTFS/lib/modules"

# Mirror
cat > "$ROOTFS/etc/apk/repositories" <<'EOF'
https://mirrors.nju.edu.cn/alpine/v3.23/main
https://mirrors.nju.edu.cn/alpine/v3.23/community
EOF
chroot_rootfs apk add alpine-base mkinitfs grub-efi