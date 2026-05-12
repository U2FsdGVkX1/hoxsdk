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
  local Sector = 512,
  local KiB = 1024 / Sector,
  local MiB = 1024 * KiB,
  local GiB = 1024 * MiB,

  partitions: [
    {
      name: 'rootfs.img',
      size: 15 * GiB,
      mkfs: 'mkfs.ext4',
      mountpoint: '/',
    },
    {
      name: 'boot.img',
      size: 1 * GiB,
      mkfs: 'mkfs.ext4',
      mountpoint: '/boot',
    },
    {
      name: 'efi.img',
      size: 500 * MiB,
      mkfs: 'mkfs.fat -F 32',
      mountpoint: '/boot/efi',
    },
  ],

  images: [
    {
      name: 'sdcard.img',
      table: 'gpt',
      partitions: [
        {
          name: 'efi.img',
          start: 1 * MiB,
          type: 'C12A7328-F81F-11D2-BA4B-00A0C93EC93B',
        },
        {
          name: 'boot.img',
          start: 1 * MiB + 500 * MiB,
          type: 'BC13C2FF-59E6-4262-A352-B275FD6F7172',
        },
        {
          name: 'rootfs.img',
          start: 1 * MiB + 500 * MiB + 1 * GiB,
          type: '0FC63DAF-8483-4772-8E79-3D69D8477DE4',
        },
      ],
    },
  ],

  target(name, actions, result, requires=[]):: {
    requires: requires,
    env: envs[arch][name],
    actions: actions,
    result: result,
  },

  opensbi(repourl, args='PLATFORM=generic', prebuild=[], postbuild=[], result=['build/platform/generic/firmware/fw_dynamic.bin'])::
    local requires = ['git', 'patch', 'make', envs[arch].opensbi.CROSS_COMPILE + 'gcc'];
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
    self.target('opensbi', actions, result, requires),

  uboot(repourl, defconfig, args='', prebuild=[], postbuild=[], result=['u-boot.bin'])::
    local requires = ['git', 'patch', 'make', envs[arch].uboot.CROSS_COMPILE + 'gcc'];
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
    self.target('uboot', actions, result, requires),

  kernel(repourl, defconfig, args='', prebuild=[], postbuild=[], result=['arch/*/boot/Image.gz', 'modules', 'dtb'])::
    local requires = ['git', 'patch', 'make', envs[arch].kernel.CROSS_COMPILE + 'gcc'];
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
    self.target('kernel', actions, result, requires),
}
