if [ "${china:-}" = "true" ]; then
    mirror="https://mirror.iscas.ac.cn/fedora"
else
    mirror="https://download.fedoraproject.org/pub/fedora/linux"
fi

case "$ARCH" in
    x86_64|amd64)
        repo_url="${mirror}/releases/44/Everything/x86_64/os/"
        ;;
    aarch64|arm64)
        repo_url="${mirror}/releases/44/Everything/aarch64/os/"
        ;;
    riscv64)
        repo_url="https://openkoji.iscas.ac.cn/kojifiles/repos/f44-build/latest/riscv64/"
        ;;
    *)
        echo "Unsupported Fedora arch: $ARCH" >&2
        return 1
        ;;
esac

if ! command -v dnf5 >/dev/null 2>&1; then
    echo "Required tool 'dnf5' not found in PATH" >&2
    return 1
fi

dnf5 --forcearch="$ARCH" \
     --disablerepo="*" \
     --repofrompath=base,"$repo_url" \
     --installroot="$ROOTFS" \
     install -y @core @hardware-support glibc-all-langpacks NetworkManager-wifi -x kernel-core -x kernel-modules -x kernel-modules-core -x kernel-modules-extra

if [ "${china:-}" = "true" ]; then
    sed -e 's|^metalink=|#metalink=|g' \
        -e "s|^#baseurl=http://download.example/pub/fedora/linux|baseurl=${mirror}|g" \
        -i.bak \
        "$ROOTFS/etc/yum.repos.d/fedora.repo" \
        "$ROOTFS/etc/yum.repos.d/fedora-updates.repo"
fi
