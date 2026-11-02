# Hox SDK

Hox SDK builds artifacts and disk images from a board config and an adapter config. It is configuration-driven: prefer changing board/adapter configs, install snippets, assets, and docs over framework code.

## Start Here

- `docs/en_US/DEVELOPER.md` — config model, modules, install snippets, debugging
- `docs/en_US/actions/` — action fields
- `boards/<board>/config.py`, `boards/common.py`, `adapters/<adapter>/`

When the docs are not enough, read the code. Don't invent config or action fields.

## Rules

- Ask the developer when the board or adapter is ambiguous, or when architecture, boot flow, partition layout, toolchain, firmware, or deployment details are missing. Don't guess them.
- Prefer the shared helpers in `boards/common.py` over hand-writing partitions, images, or firmware modules.
- If a request can't be expressed with existing configs, snippets, or actions, ask before changing `main.py`, `manager.py`, `hox.py`, `process.py`, or `actions/*.py`.
- Don't assume one board represents all boards, or that shell helpers from one adapter exist in another.
- Use `ctx.BOARD_DIR` / `ctx.ADAPTER_DIR` for local paths, never absolute workspace paths.
- Don't change unrelated files or undo unrelated changes.

## Running

- Validate config changes with `python main.py -b <board> -a <adapter> --skipbuild --skipimage --debug`. It only evaluates and prints the config.
- Ask before running anything that builds or generates images.
- When the build stage runs, `--debug` opens an interactive shell before matched build actions (all of them if no pattern is given).

## Docs

`docs/en_US/` and `docs/zh_CN/` mirror each other. Update both together and keep their structure and formatting identical.
