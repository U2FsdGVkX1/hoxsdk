local envs = {
  x86_64: {
    uboot: {
      CROSS_COMPILE: 'x86_64-linux-gnu-',
      ARCH: 'x86',
    },
    opensbi: {
      CROSS_COMPILE: 'x86_64-linux-gnu-',
      ARCH: 'x86_64',
    },
    kernel: {
      CROSS_COMPILE: 'x86_64-linux-gnu-',
      ARCH: 'x86_64',
      INSTALL_MOD_STRIP: '1',
      XZ_DEFAULTS: '--check=crc32',
    },
  },

  riscv64: {
    uboot: {
      CROSS_COMPILE: 'riscv64-linux-gnu-',
      ARCH: 'riscv',
    },
    opensbi: {
      CROSS_COMPILE: 'riscv64-linux-gnu-',
      ARCH: 'riscv',
    },
    kernel: {
      CROSS_COMPILE: 'riscv64-linux-gnu-',
      ARCH: 'riscv',
      INSTALL_MOD_STRIP: '1',
      XZ_DEFAULTS: '--check=crc32',
    },
  },

  aarch64: {
    uboot: {
      CROSS_COMPILE: 'aarch64-linux-gnu-',
      ARCH: 'arm64',
    },
    opensbi: {
      CROSS_COMPILE: 'aarch64-linux-gnu-',
      ARCH: 'arm64',
    },
    kernel: {
      CROSS_COMPILE: 'aarch64-linux-gnu-',
      ARCH: 'arm64',
      INSTALL_MOD_STRIP: '1',
      XZ_DEFAULTS: '--check=crc32',
    },
  },
};

function(arch) {
  local KiB = 1024,
  local MiB = 1024 * KiB,
  local GiB = 1024 * MiB,

  partitions: [
    {
      name: 'rootfs',
      mountpoint: '/',
      size: 15 * GiB,
      mkfs: 'mkfs.ext4',
    },
    {
      name: 'boot',
      mountpoint: '/boot',
      size: 1 * GiB,
      mkfs: 'mkfs.ext4',
    },
    {
      name: 'efi',
      mountpoint: '/boot/efi',
      size: 500 * MiB,
      mkfs: 'mkfs.fat -F 32',
    },
  ],

  target(name, actions, result, requires=[]):: {
    requires: requires,
    env: envs[arch][name],
    actions: actions,
    result: result,
  },

  opensbi(repourl, args='PLATFORM=generic', prebuild=[], postbuild=[], result=['build/platform/generic/firmware/fw_dynamic.bin'])::
    local actions = [
      {
        use: 'git',
        src: repourl,
      },
    ] + prebuild + [
      {
        use: 'make',
        args: args,
      },
    ] + postbuild;
    self.target('opensbi', actions, result, ['git', 'patch', 'make']),

  uboot(repourl, defconfig, args='', prebuild=[], postbuild=[], result=['u-boot.bin'])::
    local actions = [
      {
        use: 'git',
        src: repourl,
      },
    ] + prebuild + [
      {
        use: 'make',
        args: defconfig,
      },
      {
        use: 'make',
        args: args,
      },
    ] + postbuild;
    self.target('uboot', actions, result, ['git', 'patch', 'make']),

  kernel(repourl, defconfig, args='', prebuild=[], postbuild=[], result=['arch/*/boot/Image.gz', 'modules', 'dtb'])::
    local actions = [
      {
        use: 'git',
        src: repourl,
      },
    ] + prebuild + [
      {
        use: 'make',
        args: defconfig,
      },
      {
        use: 'make',
        args: args,
      },
      {
        use: 'make',
        args: 'INSTALL_MOD_PATH=modules DEPMOD=true modules_install',
      },
      {
        use: 'make',
        args: 'INSTALL_DTBS_PATH=dtb dtbs_install',
      },
    ] + postbuild;
    self.target('kernel', actions, result, ['git', 'patch', 'make']),
}
