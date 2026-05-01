# Hox SDK Developer Guide

## Core Files

| Path | Description |
| --- | --- |
| `main.py` | CLI entry point |
| `build_manager.py` | Build-stage scheduler |
| `image_manager.py` | Image-stage scheduler |
| `process.py` | Unified shell execution and log writing |
| `actions/` | Build-stage actions |
| `boards/` | Board configuration directory, usually containing `config.jsonnet`, `genimage.cfg`, `pre/`, `post/`, and resource files |
| `adapters/` | Distribution adapter directory, usually containing `pre/` and `post/` scripts |

## Configuration

`boards/<board>/config.jsonnet` must evaluate to a JSON object.

Minimum structure:

```jsonnet
{
  arch: 'riscv64',
  partitions: [],
  targets: {},
}
```

Top-level fields:

| Field | Type | Description |
| --- | --- | --- |
| `arch` | `string` | Target architecture, for example `aarch64` or `riscv64` |
| `partitions` | `array<object>` | List of partitions created and mounted during the image stage |
| `targets` | `object` | Build targets keyed by target name |

Common `partitions` fields:

| Field | Type | Description |
| --- | --- | --- |
| `name` | `string` | Partition image name without the `.img` suffix |
| `mountpoint` | `string` | Mount point, for example `/` or `/boot` |
| `size` | `number` | Partition size in bytes |
| `mkfs` | `string` | Filesystem creation command, for example `mkfs.ext4` |

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

- `boards/common.jsonnet` provides `partitions`, `target`, and template helpers such as `opensbi`, `uboot`, and `kernel`
- In those template helpers, `prebuild` is inserted before the default build actions, and `postbuild` is appended after them

## Action

Every action must include a `use` field. `BuildManager` loads `actions/<use>.py` and calls `run()`.

- The action working directory is always the current target working directory
- The effective environment for an action is `os.environ + target.env + .env`
- If an action writes `.env`, the new values take effect starting from the next action
- See [actions/](./actions/) for details

## Debugging

Format:

```text
TARGET[:INDEX][,...]
```

Rules:

- `INDEX` is the action index starting from `0`
- Omitting `:INDEX` is equivalent to `:*`
- `*` matches all targets or all actions
- `--debug` without a value is equivalent to `--debug '*'`
- `--skipbuild --skipimage --debug` only prints the parsed Jsonnet config and skips build/image work

Examples:

- `kernel` means `kernel:*`
- `*:0` means the `0`th action of every target
- `kernel:1` pauses only before action `1` of `kernel`

The debug shell runs in `build/<board>/<target>/`. The build resumes after the shell exits.

## Image Stage

Flow:

1. Create `build/<board>/_image/` and `rootfs/`
2. Create and mount partition images based on `partitions`
3. Run `pre` and `post` scripts
4. Unmount partitions
5. Call `genimage` to generate the final image

Rules:

- `*.sh` files are collected from both `adapters/<adapter>/<stage>/` and `boards/<board>/<stage>/`
- Scripts in the same stage run in filename order
- Scripts are loaded with `source` into the same `bash -lc` session
- The script working directory is `ROOTFS`

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
