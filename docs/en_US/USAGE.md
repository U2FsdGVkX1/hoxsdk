# Hox SDK Usage

## Common Commands

| Purpose | Command |
| --- | --- |
| Build and package an image with the default flow | `python main.py -b QEMU/Generic -a alpine` |
| Run only the build stage | `python main.py -b QEMU/Generic -a alpine --skipimage` |
| Repackage an image from existing build artifacts | `python main.py -b QEMU/Generic -a alpine --skipbuild` |

- `board` is a path relative to `boards/`, for example `QEMU/Generic`
- `adapter` is a directory name under `adapters/`, for example `fedora`

## Arguments

| Argument | Required | Description |
| --- | --- | --- |
| `-b`, `--board` | Yes | Board configuration path relative to `boards/` |
| `-a`, `--adapter` | Yes | Image adapter, mapped to `adapters/<adapter>/` |
| `--desktop` | No | Desktop profile name passed to image scripts, default is `minimal` |
| `--skipbuild` | No | Skip the build stage and run only the image stage |
| `--skipimage` | No | Skip the image stage and run only the build stage |
| `--debug` | No | Enter a debug shell before the specified `target/action`; see [DEVELOPER.md](./DEVELOPER.md#debugging) for the format |

## Outputs

| Path | Description |
| --- | --- |
| `build/<board>/<target>/` | Working directory for a target |
| `build/<board>/_image/` | Temporary working directory for the image stage |
| `outputs/<board>/` | Output directory for build artifacts and generated images |
| `logs/<board>/` | Command log directory, for example `kernel.log` and `_image.log` |

Files matched by `result` in the build stage are moved to the root of `outputs/<board>/`. Build logs are written to `logs/<board>/`.
