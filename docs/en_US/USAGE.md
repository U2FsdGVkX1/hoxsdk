# Hox SDK Usage

## Overview

Hox SDK builds artifacts and packages disk images from board and adapter configs.

```sh
python main.py -b <board> -a <adapter>
```

`<board>` is a path relative to `boards/`, `<adapter>` is a directory name under `adapters/`.

The build stage runs module `build` actions in `build/<board>/<module>/`. The image stage formats partition images, runs module `install` scripts, and writes final disk images to `outputs/<board>/`.

## Requirements

Python dependency: `pydantic` (requires Python 3.10+).

Common host tools for image generation: `sfdisk`, `dd`, `sudo`, `bash`, `mount`, `umount`.

Module `requires` may declare additional tools (e.g. `git`, `patch`, `make`, or cross compilers).

## Commands

```sh
python main.py -b <board> -a <adapter>                          # build and package
python main.py -b <board> -a <adapter> --skipimage             # build stage only
python main.py -b <board> -a <adapter> --skipbuild              # image stage only
python main.py -b <board> -a <adapter> --skipbuild --skipimage --debug  # config only
python main.py --help                                            # show help
```

Argument file support: `python main.py @args.txt`

## Arguments

| Argument | Required | Default | Description |
| --- | --- | --- | --- |
| `-b`, `--board` | Yes | None | Board path relative to `boards/` |
| `-a`, `--adapter` | Yes | None | Adapter directory name under `adapters/` |
| `--desktop` | No | `minimal` | Desktop profile name |
| `--skipbuild` | No | `false` | Skip the build stage |
| `--skipimage` | No | `false` | Skip the image stage |
| `--debug [PATTERN]` | No | Empty; `*` when used without a value | Print config and open a shell before matching build actions. See Debugging |

## Outputs

| Path | Description |
| --- | --- |
| `build/<board>/<module>/` | Per-module build workdir |
| `build/<board>/_image/` | Image-stage workdir |
| `outputs/<board>/` | Generated disk images |
| `logs/<board>/` | Command logs |

## Debugging

`--debug` prints the final config after Python DSL evaluation and pauses before matched build actions, opening an interactive shell in the module workdir.

`PATTERN` format is `MODULE[:INDEX][,...]`:

| Pattern | Meaning |
| --- | --- |
| `*` | All build actions in all modules |
| `kernel` | All build actions in the `kernel` module |
| `kernel:0` | First build action in the `kernel` module |
| `opensbi:0,kernel:0` | Multiple match positions |

Build action indexes are zero-based. When any module is matched, the build stage runs sequentially instead of concurrently.