# Hox SDK Usage

## Overview

Hox SDK builds artifacts and packages disk images from board and adapter configs.

```sh
python main.py -b <board> -a <adapter>
```

`<board>` is a path relative to `boards/`, `<adapter>` is a directory name under `adapters/`.

The build stage runs module `build` actions in `build/<board>/<module>/`. The image stage formats partition images, runs module `install` scripts, and writes final disk images to `outputs/<board>/`.

## Requirements

Python dependencies: `pydantic` and `python-dotenv` (requires Python 3.10+).

Common host tools for image generation: `sfdisk`, `dd`, `sudo`, `bash`, `mount`, `umount`.

Module `requires` may declare additional tools (e.g. `git`, `patch`, `make`, or cross compilers).

## Commands

```sh
python main.py -b <board> -a <adapter>                          # build and package
python main.py -b <board> -a <adapter> --skipimage             # build stage only
python main.py -b <board> -a <adapter> --skipbuild              # image stage only
python main.py -b <board> -a <adapter> -p KEY:VALUE             # pass a parameter
python main.py -b <board> -a <adapter> -p KEY                  # set KEY=true
python main.py -b <board> -a <adapter> --skipbuild --skipimage --debug  # config only
python main.py --help                                            # show help
```

Argument file support: `python main.py @args.txt`

## Build Parameters

`-p`/`--param KEY[:VALUE]` sets a parameter that is readable in the config DSL via `ctx.params["KEY"]` and exported as the environment variable `$KEY` in image-stage install snippets.

## Options

| Option | Required | Default | Description |
| --- | --- | --- | --- |
| `-b`, `--board` | Yes | None | Board path relative to `boards/` |
| `-a`, `--adapter` | Yes | None | Adapter directory name under `adapters/` |
| `--desktop` | No | `minimal` | Desktop profile name |
| `--skipbuild` | No | `false` | Skip the build stage |
| `--skipimage` | No | `false` | Skip the image stage |
| `-p`, `--param KEY[:VALUE]` | No | None | Set a parameter; see Build Parameters |
| `--debug [PATTERN]` | No | Empty | Print config and open a shell before matching build actions. See Debugging |

## Outputs

| Path | Description |
| --- | --- |
| `build/<board>/<module>/` | Per-module build workdir |
| `build/<board>/_image/` | Image-stage workdir |
| `outputs/<board>/` | Generated disk images |
| `logs/<board>/` | Command logs |

## Debugging

`--debug` prints the final config and opens a shell before matched build actions.

```sh
python main.py -b <board> -a <adapter> --debug 'kernel:*' --debug 'uboot:1'
```
