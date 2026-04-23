# Hox SDK Config

## Scope

- Write or adjust Hox SDK config files.
- Focus on `boards/<board>/`, `adapters/<adapter>/`, `genimage.cfg`, board assets, and scripts.

## Boundaries

- Do not modify the main program: `main.py`, `build_manager.py`, `image_manager.py`, `process.py`, `actions/*.py`.
- Only touch core implementation if the user explicitly asks.
- Prefer debugging through `build/`, `outputs/`, `logs/`, or `--debug` shells in build directories.

## Read First

- `docs/en_US/USAGE.md`
- `docs/en_US/DEVELOPER.md`
- Current board config: `boards/<board>/config.jsonnet`
- Shared templates: `boards/common.jsonnet`
- Current adapter and board scripts: `adapters/<adapter>/{pre,post}/`, `boards/<board>/{pre,post}/`
- If action details are needed, read `docs/en_US/actions/*.md` and the matching `actions/*.py`; do not hardcode the current action list, fields, or count

## Mental Model

- Entry command: `python main.py -b <board> -a <adapter>`
- `config.jsonnet` must at least return `{ arch, partitions, targets }`
- Build stage: `targets` form a dependency graph; actions inside one target run in order; the working directory is `build/<board>/<target>/`; `result` files go to `outputs/<board>/`.
- Image stage: create partitions from `partitions`, then run adapter and board `pre`/`post` scripts in filename order; scripts are `source`d in one shell session and run in `ROOTFS`.

## Development Rules

- Reuse `boards/common.jsonnet` and the closest existing board config first.
- Prefer config and script changes over framework changes.
- For a new target, add only the minimum needed fields: `requires`, `depends`, `env`, `actions`, `result`.
- Do not guess action behavior; read docs and existing examples first.
- If required board, adapter, partition, toolchain, artifact, or boot-flow details are missing, ask the user first. Only continue writing once the needed inputs are clear enough.
- If environment must flow across actions, use `.env`; it is reloaded before the next action.
- Keep changes small and follow existing names, layout, and script numbering.
- Before writing config, state which existing board, adapter, or action pattern you are following.

## Debugging

- Build only: `python main.py -b <board> -a <adapter> --skipimage`
- Image only: `python main.py -b <board> -a <adapter> --skipbuild`
- Break before an action: `python main.py -b <board> -a <adapter> --debug <target[:index]>`
- Check first: `logs/<board>/`, `outputs/<board>/`, `build/<board>/`
