# Hox SDK Developer Guide

## Concepts

The SDK drives builds and image generation by composing a **board config** and an **adapter config**.

- **Board config** (`boards/<board>/config.py`): defines architecture, partitions, disk images, and a module list.
- **Adapter config** (`adapters/<adapter>/config.py`): provides distribution-related modules.
- **Module**: a pluggable build (`build`) and install (`install`) unit, ordered by `build_after`, `build_before`, `install_after`, and `install_before`.
- **Action**: a build action within a module. Implementations live in `actions/`; field docs live in `docs/en_US/actions/`.
- **Install snippet**: an install unit within a module, run during image generation to customize the root filesystem.

Run command:

```sh
python main.py -b <board> -a <adapter>
```

`<board>` is a path relative to `boards/`, `<adapter>` is a directory name under `adapters/`.

## Writing a Board Config

Board configs are Python DSL files exporting `configure(ctx) -> Board`. Key `ConfigContext` attributes:

- `ctx.adapter` — load the selected adapter's module list.
- `ctx.module(name, *args)` — load a board-local module: runs `modules/<name>/config.py` and returns its `configure(ctx, *args)`.
- `ctx.BOARD_DIR` — absolute path to the board directory; use `ctx.BOARD_DIR / "file"` for board-local files.
- `ctx.ADAPTER_DIR` — absolute path to the adapter directory; use `ctx.ADAPTER_DIR / "file"` for adapter-local files (mainly in adapter configs).
- `ctx.ADAPTER_NAME` — selected adapter name string.

A minimal board config:

```python
from boards.common import default_images, default_partitions
from hox import Board, ConfigContext


def configure(ctx: ConfigContext) -> Board:
    arch = "riscv64"
    return Board(
        arch=arch,
        partitions=default_partitions(),
        images=default_images(),
        modules=ctx.adapter,
    )
```

### Top-Level Fields

| Field | Required | Purpose |
| --- | --- | --- |
| `arch` | Yes for image generation | Target architecture, passed as `ARCH` to install snippets |
| `partitions` | No | Partition image definitions |
| `images` | No | Final disk image definitions |
| `modules` | No | Build and install module list |

### `partitions` Fields

| Field | Required | Purpose |
| --- | --- | --- |
| `name` | Yes | Partition image file name |
| `size` | Yes | Partition size in 512-byte sectors |
| `mkfs` | Yes | Filesystem command, for example `mkfs.ext4` |
| `mountpoint` | Yes | Mount point inside the temporary rootfs |

### `images` Fields

| Field | Required | Purpose |
| --- | --- | --- |
| `name` | Yes | Final image file name under `outputs/<board>/` |
| `table` | No | Partition table type: `gpt` or `dos`; default is `gpt` |
| `partitions` | Yes | Partition references in final image order |

### `images[].partitions` Fields

| Field | Required | Purpose |
| --- | --- | --- |
| `name` | Yes | Partition image file name |
| `start` | Yes | Start offset in 512-byte sectors |
| `size` | No | Size in sectors; omitted values are inferred from the partition image file |
| `type` | No | Partition type passed to `sfdisk` |
| `bootable` | No | Marks the partition bootable when supported by the table type |

## Modules

Modules are `Module(...)` values. Board configs compose adapter modules with board modules; execution order is determined by `build_after`, `build_before`, `install_after`, and `install_before`.

| Field | Default | Purpose |
| --- | --- | --- |
| `name` | Required | Unique name; also used as build workdir when `build` actions are present |
| `build_after` | `[]` | Module names that must finish building before this module starts building |
| `build_before` | `[]` | Module names that must build after this module |
| `install_after` | `[]` | Module names that must finish installing before this module starts installing |
| `install_before` | `[]` | Module names that must install after this module; useful for inserting board modules before adapter finalization steps |
| `requires` | `[]` | Host commands that must exist before the module runs |
| `env` | `{}` | Environment variables passed to build actions |
| `build` | `[]` | Build action list |
| `install` | `[]` | Install items; `Path` values are sourced as scripts, `str` values are run as shell commands |

Build module example:

```python
Module(
    name="firmware",
    requires=["make"],
    env={"ARCH": "arm64", "CROSS_COMPILE": "aarch64-linux-gnu-"},
    build=[make(args="defconfig"), make()],
)
```

Install module example:

```python
Module(
    name="board-customization",
    install_after=["image-fstab"],
    install=[
        "echo hello",
        ctx.BOARD_DIR / "200-customization.sh",
    ],
)
```

- Modules with `build` actions run in `build/<board>/<module>/`; the workdir is recreated each time.
- Build actions within a module run in order; a `.env` file written by one action passes variables to later build actions in the same module.
- During build, modules whose `build_after` and `build_before` constraints are all satisfied run concurrently.
- Install snippets run during image generation in topological order determined by `install_after` and `install_before`, and can access build artifacts via `MODULE_DIR` and `BUILD_DIR`.

## Install Snippets

Referenced in a module's `install` list. `str` values are executed directly as shell commands; `Path` values are sourced as scripts. Adapter snippets go in `adapters/<adapter>/`, board snippets go in `boards/<board>/`, and shared snippets go in `boards/`.

All snippets run in one shell session in topological order determined by `install_after`, working directory `ROOTFS`. Functions and variables defined by earlier snippets are available to later ones.

| Variable | Purpose |
| --- | --- |
| `ROOTFS` | Temporary root filesystem directory |
| `BOARD_NAME` | Current board directory name |
| `BOARD_DIR` | Absolute path to the current board directory |
| `ADAPTER_NAME` | Current adapter name |
| `ADAPTER_DIR` | Absolute path to the current adapter directory |
| `MODULE_DIR` | Absolute path to `build/<board>/<module>/` for the module currently contributing install snippets |
| `BUILD_DIR` | Absolute path to `build/<board>/` |
| `OUTPUT_DIR` | Absolute path to `outputs/<board>/` |
| `ARCH` | Board architecture from `config.py` |

## Shared Helpers

`boards/common.py` provides shared defaults and firmware templates:

- `default_partitions()` — standard partition layout (rootfs, boot, efi).
- `default_images()` — standard disk image layout (sdcard.img).
- `firmware(arch)` — returns a namespace with `opensbi`, `uboot`, and `kernel` factory functions. Common parameters: `src`, `args`, `prebuild`, `postbuild`, `install`, `build_after`, `build_before`, `install_after`, `install_before`. Additionally, `uboot` and `kernel` accept `defconfig`.

Import API types from `hox` and action constructors from `actions`:

```python
from hox import Board, ConfigContext, Module
from actions import make
```

Board configs load the selected adapter with `ctx.adapter`.

## Actions

Each action module exports an `Action` class, and `actions/__init__.py` re-exports common constructors for config use: `from actions import git, make, cp, patch, shell`. `BaseAction.use` is derived from the module name.

## Debugging

Print the final config without running builds or image generation:

```sh
python main.py -b <board> -a <adapter> --skipbuild --skipimage --debug
```

Pause before matched module build actions and open an interactive shell:

```sh
python main.py -b <board> -a <adapter> --debug <pattern>
```

Effects of `--debug`:

- Prints the final config after Python DSL evaluation and Pydantic validation.
- When a matched build action is reached, opens a shell in `build/<board>/<module>/` with environment variables from module `env` and any `.env` file. Execution continues after exiting the shell.
- When any module is matched, the build stage runs modules sequentially instead of concurrently, making debugging easier.

`<pattern>` format is `MODULE[:INDEX][,...]`, matching multiple positions at once:

| Pattern | Meaning |
| --- | --- |
| `*` | All build actions in all modules |
| `kernel` | All build actions in the `kernel` module |
| `kernel:0` | First build action in the `kernel` module |
| `*:1` | Second build action in every module |
| `opensbi:0,kernel:0` | First build action in `opensbi` and first build action in `kernel` |

When no value is given, the default pattern is `*`. Build action indexes are zero-based.