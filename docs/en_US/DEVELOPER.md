# Hox SDK Developer Guide

## Core Files

| Path | Description |
| --- | --- |
| `main.py` | CLI entry point |
| `build_manager.py` | Build-stage scheduler |
| `image_manager.py` | Image-stage scheduler |
| `process.py` | Unified shell execution and log writing |
| `actions/` | Build-stage actions |
| `boards/` | Board configuration directory, usually containing `config.jsonnet`, `pre/`, `post/`, and resource files |
| `adapters/` | Distribution adapter directory, usually containing `pre/` and `post/` scripts |

## Configuration

`boards/<board>/config.jsonnet` must evaluate to a JSON object.

Minimum structure:

```jsonnet
{
  arch: 'riscv64',
  partitions: [],
  images: [],
  targets: {},
}
```

Top-level fields:

| Field | Type | Description |
| --- | --- | --- |
| `arch` | `string` | Target architecture, for example `aarch64` or `riscv64` |
| `partitions` | `array<object>` | Partition images to create, format, and mount |
| `images` | `array<object>` | Final disk image definitions |
| `targets` | `object` | Build targets keyed by target name |

Top-level `partitions` entry fields:

| Field | Type | Description |
| --- | --- | --- |
| `name` | `string` | Partition image file name, for example `rootfs.img` |
| `size` | `number` | Partition size in sectors |
| `mkfs` | `string` | Filesystem creation command |
| `mountpoint` | `string` | Mount point; the image is created and mounted before rootfs installation |

`images` entry fields:

| Field | Type | Description |
| --- | --- | --- |
| `name` | `string` | Final disk image file name, for example `sdcard.img` |
| `table` | `string` | Partition table type, for example `gpt` or `dos` |
| `partitions` | `array<object>` | Partition reference list in final disk order |

`images[].partitions` entry fields:

| Field | Type | Description |
| --- | --- | --- |
| `name` | `string` | Partition image file name in the image work directory |
| `start` | `number` | Partition start offset in sectors |
| `size` | `number` | Partition image size in sectors; auto-detected from file size when omitted |
| `type` | `string` | Partition type passed to `sfdisk`, for example a GPT type UUID |

### Target

| Field | Type | Default | Description |
| --- | --- | --- | --- |
| `requires` | `array<string>` | `[]` | Host commands checked before execution |
| `depends` | `array<string>` | `[]` | Names of other targets this target depends on |
| `env` | `object` | `{}` | Environment variables passed to actions |
| `actions` | `array<object>` | `[]` | Action list executed in order |
| `result` | `array<string>` | `[]` | Globs collected from the working directory and moved to `outputs/<board>/` after the build finishes |

Example:

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
        { use: 'git', src: 'https://github.com/torvalds/linux' },
        { use: 'make', args: 'defconfig' },
        { use: 'make' },
      ],
      result: ['arch/*/boot/Image.gz'],
    },
  },
}
```

Rules:

- By default, targets are scheduled concurrently according to their dependency graph
- With `--debug`, targets wait one by one to make interactive debugging practical
- `actions` inside the same target always run strictly in order
- Each target works in `build/<board>/<target>/`, which is recreated before every build
- Before each action runs, `.env` is reloaded and overrides variables with the same name from `target.env`
- Files or directories matched by `result` are moved to the root of `outputs/<board>/`
- `BDIR` is the absolute path to the current board directory

Helpers:

- `boards/common.jsonnet` provides `partitions`, `images`, `target`, and template helpers such as `opensbi`, `uboot`, and `kernel`
- In those template helpers, `prebuild` is inserted before the default build actions, and `postbuild` is appended after them

## Action

Every action must include a `use` field. `BuildManager` loads `actions/<use>.py` and calls `run()`.

- The action working directory is always the current target working directory
- The effective environment for an action is `os.environ + target.env + .env`
- If an action writes `.env`, the new values take effect starting from the next action
- See [actions/](./actions/) for details

## Debugging

`--debug` accepts breakpoint patterns in this format:

```text
TARGET[:INDEX][,...]
```

- `*` matches all targets or actions
- `kernel` means `kernel:*`
- `*:1` matches action `1` on all targets
- `kernel:*` matches all `kernel` actions
- `kernel:1` matches action `1` on `kernel`

`--debug` without a value is equivalent to `--debug '*'`. Use `--skipbuild --skipimage --debug` to print only the parsed Jsonnet config.

## Image Stage

Flow:

1. Create `build/<board>/_image/` and `rootfs/`
2. Create and mount partition images from top-level `partitions` entries with `mountpoint`
3. Run `pre` and `post` scripts
4. Unmount partitions
5. Write final disk images from `images` using `sfdisk`

Rules:

- `*.sh` files are collected from both `adapters/<adapter>/<stage>/` and `boards/<board>/<stage>/`
- Scripts in the same stage run in filename order
- The script working directory is `ROOTFS`
- `images[].name` is used as the final disk image output name
- Do not define external images in top-level `partitions`; reference their file name directly from `images[].partitions[]`; `size` may be provided explicitly or omitted to auto-detect from file size

Script environment variables:

| Variable | Description |
| --- | --- |
| `ROOTFS` | Temporary root filesystem directory |
| `BOARD_NAME` | Name of the current board directory |
| `BOARD_DIR` | Absolute path to the current board directory |
| `ADAPTER_NAME` | Current adapter name |
| `ADAPTER_DIR` | Absolute path to the current adapter directory |
| `BUILD_DIR` | Absolute path to the current board build directory |
| `OUTPUT_DIR` | Absolute path to the current board output directory |
| `FIRMWARE_DIR` | Currently the same as `OUTPUT_DIR` |
| `ARCH` | Target architecture |
| `DESKTOP` | Desktop profile name passed from the command line |
