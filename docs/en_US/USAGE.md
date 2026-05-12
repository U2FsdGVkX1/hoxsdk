# Hox SDK Usage

## Overview

Hox SDK builds board artifacts and packages disk images from board configs and adapter scripts.

A run selects:

- A board config from `boards/<board>/config.jsonnet`.
- An image adapter from `adapters/<adapter>/`.

The build stage writes artifacts to `outputs/<board>/`. The image stage uses those artifacts and writes final disk images to the same output directory.

## Available Boards And Adapters

Boards currently present in this repository:

| Board argument | Config |
| --- | --- |
| `QEMU/Generic` | `boards/QEMU/Generic/config.jsonnet` |
| `AMLogic-S905D5/VSAI-BQ201` | `boards/AMLogic-S905D5/VSAI-BQ201/config.jsonnet` |

Adapters currently present in this repository:

| Adapter argument | Path |
| --- | --- |
| `alpine` | `adapters/alpine/` |
| `fedora` | `adapters/fedora/` |

## Requirements

Root Python dependencies:

- Python 3.10+
- `_jsonnet`
- `pydantic`

Common host tools used by image generation:

- `sfdisk`
- `dd`
- `sudo`
- `bash`
- `mount`
- `umount`

Board targets may require additional tools such as `git`, `patch`, `make`, or cross compilers. Check `requires` in the selected board config.

Dependency installation commands are Unknown because this repository does not provide root package metadata.

## Commands

Show CLI help:

```sh
python main.py --help
```

Build and package an image:

```sh
python main.py -b QEMU/Generic -a alpine
```

Run only the build stage:

```sh
python main.py -b QEMU/Generic -a alpine --skipimage
```

Run only the image stage from existing outputs:

```sh
python main.py -b QEMU/Generic -a alpine --skipbuild
```

Print the final JSON config produced after Jsonnet evaluation, without building or packaging:

```sh
python main.py -b QEMU/Generic -a alpine --skipbuild --skipimage --debug
```

Use an argument file:

```sh
python main.py @args.txt
```

## Arguments

| Argument | Required | Default | Description |
| --- | --- | --- | --- |
| `-b`, `--board` | Yes | None | Board path relative to `boards/` |
| `-a`, `--adapter` | Yes | None | Adapter directory name under `adapters/` |
| `--desktop` | No | `minimal` | Desktop profile name passed to image scripts |
| `--skipbuild` | No | `false` | Skip the build stage |
| `--skipimage` | No | `false` | Skip the image stage |
| `--debug [TARGET[:INDEX][,...]]` | No | Empty; `*` when used without a value | Print config and open a shell before matching actions |

## Outputs

| Path | Description |
| --- | --- |
| `build/<board>/<target>/` | Per-target build workdir |
| `build/<board>/_image/` | Image-stage workdir |
| `outputs/<board>/` | Build artifacts and generated images |
| `logs/<board>/` | Command logs |

## Notes

- Board names are paths relative to `boards/`.
- Adapter names are directory names under `adapters/`.
- The shared default final image name is `sdcard.img` when using `boards/common.jsonnet` defaults.
- Needs verification: Fedora adapter post scripts call `chroot_rootfs`, but no Fedora-local definition was found.
