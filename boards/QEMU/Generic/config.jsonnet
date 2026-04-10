local arch = 'riscv64';
local common = (import './common.jsonnet')(arch);

{
  arch: arch,
  partitions: common.partitions,
  targets: {
    opensbi: common.opensbi('https://github.com/riscv-software-src/opensbi'),
    uboot: common.uboot('https://github.com/u-boot/u-boot', 'qemu-riscv64_smode_defconfig'),
    kernel: common.kernel('https://github.com/torvalds/linux', 'defconfig'),
  },
}
