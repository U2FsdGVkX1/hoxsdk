case "$ARCH" in
    x86_64|amd64)
        repo_url="https://download.fedoraproject.org/pub/fedora/linux/development/rawhide/Everything/x86_64/os/"
        ;;
    aarch64|arm64)
        repo_url="https://download.fedoraproject.org/pub/fedora/linux/development/rawhide/Everything/aarch64/os/"
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
     install -y @core @hardware-support glibc-all-langpacks -x kernel-core -x kernel-modules -x kernel-modules-core -x kernel-modules-extra