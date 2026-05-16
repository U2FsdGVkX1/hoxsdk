# Hox SDK Skill

## Purpose

Use this skill when helping with Hox SDK board configs, adapter configs, modules, image customization, actions, or SDK documentation.

The SDK is configuration-driven. Prefer changes to board configs, adapter configs, install snippets, assets, and docs before changing framework code.

## Core Rule

If required information is unknown, ask the developer before acting. Do not guess architecture, board name, adapter name, boot flow, partition layout, toolchain, artifact names, firmware paths, environment variables, deployment steps, or action behavior.

## Boundaries

- Do not modify `main.py`, `manager.py`, `hox.py`, `process.py`, or `actions/*.py` unless the developer explicitly asks for framework changes or a new action is truly required.
- Do not assume one existing board represents all supported boards.
- Do not run full builds or image generation unless the developer asks or explicitly approves it.
- Do not rewrite unrelated files or undo unrelated changes.

## Read First

- `docs/en_US/DEVELOPER.md`
- Current board config: `boards/<board>/config.py`
- Shared helpers: `boards/common.py`
- Relevant adapter config and install snippets: `adapters/<adapter>/config.py` and `adapters/<adapter>/*.sh`
- Action docs in `docs/en_US/actions/` when action fields are needed

## Mental Model

- Entry: `python main.py -b <board> -a <adapter>`
- `board` is a path relative to `boards/`; `adapter` is a directory name under `adapters/`
- `boards/<board>/config.py` should export `configure(ctx)` and use `ctx.adapter` to load the selected adapter's module list
- `ctx.BOARD_DIR` is the absolute path to the selected board directory
- Modules use `build_after` and `install_after` for sequencing; modules without unsatisfied dependencies run concurrently during build
- Build artifacts live under `build/<board>/<module>/` and are available to install snippets via `MODULE_DIR` or `BUILD_DIR`
- Install snippets are declared as file paths in module `install` arrays
- `--debug` prints the final config; with a pattern it opens an interactive shell before matched actions and forces sequential build execution

## Config Rules

- Preserve config field names exactly: `partitions`, `images`, `images[].partitions`, `modules`, etc.
- Use `ctx.BOARD_DIR` for board-local paths instead of absolute workspace paths
- Use `.env` only when one action must pass values to later actions in the same module
- Prefer action constructors imported from `actions`, such as `from actions import git` and `git(src=...)`; do not invent action fields — read `docs/en_US/actions/` or `actions/<use>.py`

## Image Script Rules

- Adapter snippets go under `adapters/<adapter>/`; board snippets go under `boards/<board>/`
- Use module `install_after` to control install order
- Use documented environment variables (`ROOTFS`, `BOARD_DIR`, `ADAPTER_DIR`, `MODULE_DIR`, `BUILD_DIR`, `OUTPUT_DIR`, `ARCH`)
- Do not assume helper shell functions exist across adapters

## Ask Before Acting

Ask the developer when:

- The board or adapter is ambiguous
- Required boot, partition, toolchain, firmware, or deployment details are missing
- The requested behavior cannot be expressed with existing config, scripts, or actions
- A full build or image generation may be needed
