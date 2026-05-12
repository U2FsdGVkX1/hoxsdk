# Hox SDK Developer Guide

## Purpose

This guide explains how to add or maintain SDK board configs, build targets, actions, and image scripts.

## Repository Layout

| Path | Purpose |
| --- | --- |
| `main.py` | SDK command entry point |
| `boards/` | Board definitions and board-specific assets |
| `boards/common.jsonnet` | Shared Jsonnet helpers for common partitions, images, and build targets |
| `adapters/` | Root filesystem and image customization scripts for distributions |
| `actions/` | Reusable build actions |
| `docs/en_US/actions/` | Reference docs for action fields |
| `build/` | Generated working directories |
| `outputs/` | Generated artifacts and disk images |
| `logs/` | Command logs |

Primary formats used by SDK authors:

- Jsonnet for board configuration
- Shell scripts for image customization
- Python for SDK framework actions and command orchestration

## Add Or Update A Board

A board lives under `boards/<board>/`, where `<board>` is the value passed to `python main.py -b`.

Required file:

| Path | Purpose |
| --- | --- |
| `boards/<board>/config.jsonnet` | Board architecture, build targets, partition layout, and final image layout |

Optional board directories:

| Path | Purpose |
| --- | --- |
| `boards/<board>/pre/` | Board scripts run during the image pre stage |
| `boards/<board>/post/` | Board scripts run during the image post stage |
| Other board-local paths | Patches, overlays, firmware, or other board assets referenced by config or scripts |

`main.py` passes `BDIR` to Jsonnet as the absolute board directory path. Use it when a config needs to reference board-local files:

```jsonnet
local BDIR = std.extVar('BDIR');
```

Minimal board config:

```jsonnet
{
  arch: 'riscv64',
  partitions: [],
  images: [],
  targets: {},
}
```

## Board Config Fields

Top-level fields:

| Field | Required | Purpose |
| --- | --- | --- |
| `arch` | Yes for image generation | Target architecture passed to image scripts as `ARCH` |
| `partitions` | No | Partition images to create, format, and mount before scripts run |
| `images` | No | Final disk images to write |
| `targets` | No | Build targets keyed by target name |

Partition fields:

| Field | Required | Purpose |
| --- | --- | --- |
| `name` | Yes | Partition image file name |
| `size` | Yes | Partition size in 512-byte sectors |
| `mkfs` | Yes | Filesystem command, for example `mkfs.ext4` |
| `mountpoint` | Yes | Mount point inside the temporary rootfs |

Image fields:

| Field | Required | Purpose |
| --- | --- | --- |
| `name` | Yes | Final image file name under `outputs/<board>/` |
| `table` | No | Partition table type: `gpt` or `dos`; default is `gpt` |
| `partitions` | Yes | Partition references in final image order |

Image partition fields:

| Field | Required | Purpose |
| --- | --- | --- |
| `name` | Yes | Partition image file name |
| `start` | Yes | Start offset in 512-byte sectors |
| `size` | No | Size in sectors; omitted values are inferred from the partition image file |
| `type` | No | Partition type passed to `sfdisk` |
| `bootable` | No | Marks the partition bootable when supported by the table type |

## Build Targets

Each target describes one build unit.

| Field | Default | Purpose |
| --- | --- | --- |
| `requires` | `[]` | Host commands that must exist before the target runs |
| `depends` | `[]` | Other targets that must complete first |
| `env` | `{}` | Environment variables passed to actions |
| `actions` | `[]` | Ordered build action list |
| `result` | `[]` | Glob patterns copied out of the target workdir into `outputs/<board>/` |

Example target:

```jsonnet
{
  targets: {
    kernel: {
      requires: ['make'],
      env: {
        ARCH: 'arm64',
        CROSS_COMPILE: 'aarch64-linux-gnu-',
      },
      actions: [
        { use: 'make', args: 'defconfig' },
        { use: 'make' },
      ],
      result: ['arch/*/boot/Image.gz'],
    },
  },
}
```

Target rules:

- Targets run in `build/<board>/<target>/`.
- Each target workdir is recreated before the target runs.
- Target dependencies are declared with `depends`.
- Actions inside one target run in order.
- Files matched by `result` are moved to `outputs/<board>/`.
- A `.env` file written by one action can pass variables to later actions in the same target.

## Shared Helpers

Prefer `boards/common.jsonnet` when it fits the board.

Available helpers:

| Helper | Purpose |
| --- | --- |
| `partitions` | Shared `rootfs.img`, `boot.img`, and `efi.img` partition definitions |
| `images` | Shared `sdcard.img` image definition |
| `target(...)` | Creates a target with shared architecture environment values |
| `opensbi(...)` | Common OpenSBI build target template |
| `uboot(...)` | Common U-Boot build target template |
| `kernel(...)` | Common Linux kernel build target template |

The template helpers accept `prebuild` and `postbuild` action lists for board-specific adjustments.

## Actions

Actions are selected by the `use` field.

Action implementations live in `actions/`. Action field documentation lives in `docs/en_US/actions/`.

When adding a target, use an existing action before adding a new one. If a new action is required, add `actions/<name>.py` and document its fields under `docs/en_US/actions/<name>.md`.

## Image Scripts

Image scripts customize the temporary root filesystem and final image inputs.

Script locations:

| Path | Purpose |
| --- | --- |
| `adapters/<adapter>/pre/*.sh` | Adapter pre-stage scripts |
| `boards/<board>/pre/*.sh` | Board pre-stage scripts |
| `adapters/<adapter>/post/*.sh` | Adapter post-stage scripts |
| `boards/<board>/post/*.sh` | Board post-stage scripts |

Script rules:

- `pre` runs before `post`.
- Adapter and board scripts are both included.
- Scripts in each stage run in filename order.
- Scripts run in one shell session, so functions defined by earlier scripts can be used by later scripts.
- The script working directory is `ROOTFS`.

Script environment variables:

| Variable | Purpose |
| --- | --- |
| `ROOTFS` | Temporary root filesystem directory |
| `BOARD_NAME` | Current board directory name |
| `BOARD_DIR` | Absolute path to the current board directory |
| `ADAPTER_NAME` | Current adapter name |
| `ADAPTER_DIR` | Absolute path to the current adapter directory |
| `BUILD_DIR` | Absolute path to `build/<board>/` |
| `OUTPUT_DIR` | Absolute path to `outputs/<board>/` |
| `FIRMWARE_DIR` | Same value as `OUTPUT_DIR` |
| `ARCH` | Board architecture from `config.jsonnet` |
| `DESKTOP` | Value passed with `--desktop` |

## Debugging

Print the final JSON config produced after Jsonnet evaluation, without running build or image stages:

```sh
python main.py -b <board> -a <adapter> --skipbuild --skipimage --debug
```

Open a debug shell before matching actions:

```sh
python main.py -b <board> -a <adapter> --debug <target[:index]>
```

Patterns:

| Pattern | Meaning |
| --- | --- |
| `*` | All targets and actions |
| `kernel` | All actions in `kernel` |
| `kernel:0` | First action in `kernel` |
| `*:1` | Second action in every target |

Action indexes are zero-based.

## Validation

Useful checks after changing SDK configs:

```sh
python main.py --help

# check the final JSON config produced from `boards/<board>/config.jsonnet`.
python main.py -b <board> -a <adapter> --skipbuild --skipimage --debug
```