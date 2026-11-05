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
python main.py -b <board> -a <adapter>                                  # build and package
python main.py -b <board> -a <adapter> --skipimage                      # build stage only
python main.py -b <board> -a <adapter> --skipbuild                      # image stage only
python main.py -b <board> -a <adapter> --skipimage -m <module>          # build selected modules only
python main.py -b <board> -a <adapter> -p KEY:VALUE                     # pass a parameter
python main.py -b <board> -a <adapter> -p KEY                           # set KEY=true
python main.py -b <board> -a <adapter> --skipbuild --skipimage --debug  # config only
python main.py --help                                                   # show help
```

Argument file support: `python main.py @args.txt`

## Build Parameters

`-p`/`--param KEY[:VALUE]` sets a parameter that is readable in the config DSL via `ctx.params["KEY"]` and exported as the environment variable `$KEY` in image-stage install snippets.

## Building Selected Modules

`-m`/`--module PATTERN` limits the build stage to modules whose names match `PATTERN`. Patterns accept shell-style wildcards, and the option is repeatable:

```sh
python main.py -b <board> -a <adapter> --skipimage -m mesa -m 'img-*'
```

- Only matching modules are rebuilt; the build workdirs of other modules are left as they are.
- Matching modules do not wait for unselected modules in `build_after`/`build_before`; the existing build output of those modules is used.
- The image stage is not filtered: it still runs the install snippets of every module, so every module needs build output.

## Options

| Option | Required | Default | Description |
| --- | --- | --- | --- |
| `-b`, `--board` | Yes | None | Board path relative to `boards/` |
| `-a`, `--adapter` | Yes | None | Adapter directory name under `adapters/` |
| `--desktop` | No | `minimal` | Desktop profile name |
| `--skipbuild` | No | `false` | Skip the build stage |
| `--skipimage` | No | `false` | Skip the image stage |
| `-m`, `--module PATTERN` | No | None | Build only matching modules; see Building Selected Modules |
| `-p`, `--param KEY[:VALUE]` | No | None | Set a parameter; see Build Parameters |
| `--debug [PATTERN]` | No | Empty | Print config and open a shell before matching build actions; see [Debugging](DEVELOPER.md#debugging) |

## Outputs

| Path | Description |
| --- | --- |
| `build/<board>/<module>/` | Per-module build workdir |
| `build/<board>/_image/` | Image-stage workdir |
| `outputs/<board>/` | Generated disk images |
| `logs/<board>/` | Command logs |
