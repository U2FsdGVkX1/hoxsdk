# Hox SDK Skill

## Purpose

Use this skill when helping with Hox SDK board configs, adapter scripts, image customization, build targets, actions, or SDK documentation.

The SDK is configuration-driven. Prefer changes to board configs, adapter scripts, board scripts, assets, and docs before changing framework code.

## Core Rule

If required information is unknown, ask the developer before acting.

Do not guess architecture, board name, adapter name, boot flow, partition layout, toolchain, artifact names, firmware paths, package sources, environment variables, deployment steps, or action behavior. Ask a concise question and continue only after the missing detail is clear.

## Boundaries

- Do not modify `main.py`, `build_manager.py`, `image_manager.py`, `process.py`, or `actions/*.py` unless the developer explicitly asks for framework changes or a new action is truly required.
- Do not assume one existing board represents all supported boards.
- Do not hardcode the current action list in high-level docs; point developers to `actions/` and `docs/en_US/actions/`.
- Do not run full builds or image generation unless the developer asks or explicitly approves it.
- Do not rewrite unrelated files or undo unrelated changes.

## Read First

- `docs/en_US/USAGE.md`
- `docs/en_US/DEVELOPER.md`
- Current board config: `boards/<board>/config.jsonnet`
- Shared helpers: `boards/common.jsonnet`
- Relevant adapter scripts: `adapters/<adapter>/pre/` and `adapters/<adapter>/post/`
- Relevant board scripts: `boards/<board>/pre/` and `boards/<board>/post/`
- Action docs in `docs/en_US/actions/` when action fields are needed

## Mental Model

- Entry command: `python main.py -b <board> -a <adapter>`.
- `board` is a path relative to `boards/`.
- `adapter` is a directory name under `adapters/`.
- `boards/<board>/config.jsonnet` produces the final SDK configuration.
- `BDIR` is available in Jsonnet as the absolute path to the selected board directory.
- Build targets are declared under `targets`.
- Target dependencies use `depends`.
- Target actions run in order.
- Target `result` entries move artifacts into `outputs/<board>/`.
- Image scripts come from both adapter and board `pre/` and `post/` directories.
- Final disk images are declared under `images`; partition images are declared under `partitions`.

## Workflow

- Identify the target board and adapter before editing.
- If board or adapter choice affects the task and is not specified, ask the developer.
- Inspect the closest relevant existing board or adapter before creating a new one.
- Reuse `boards/common.jsonnet` when it fits the requested layout or build flow.
- Prefer small config and script changes over framework changes.
- Keep board-specific assumptions inside the relevant board directory.
- Keep distribution-specific assumptions inside the relevant adapter directory.
- Verify every documented command, file path, field, and environment variable against repository files.

## Config Rules

- Preserve config field names exactly in explanations and docs, such as `partitions`, `images`, `images[].partitions`, and `targets`.
- Use `BDIR` for board-local paths instead of absolute workspace paths.
- For a new target, add only the fields needed: `requires`, `depends`, `env`, `actions`, and `result`.
- Use `requires` for host tools that must exist before a target runs.
- Use `depends` for build ordering.
- Use `env` for variables passed to actions.
- Use `.env` only when one action must pass generated values to later actions in the same target.
- Use `result` for artifacts that should be moved from `build/<board>/<target>/` to `outputs/<board>/`.

## Action Rules

- Every action entry must include `use`.
- Read the matching action documentation before using an action.
- If the documentation is missing or unclear, read `actions/<use>.py`.
- Do not invent action fields.

## Image Script Rules

- Adapter scripts belong under `adapters/<adapter>/pre/` or `adapters/<adapter>/post/`.
- Board scripts belong under `boards/<board>/pre/` or `boards/<board>/post/`.
- Use filename prefixes to control script order.
- Use documented script environment variables such as `ROOTFS`, `BOARD_DIR`, `ADAPTER_DIR`, `BUILD_DIR`, `OUTPUT_DIR`, `FIRMWARE_DIR`, `ARCH`, and `DESKTOP`.
- Do not assume helper shell functions exist across adapters unless their definition and load order are verified.

## Debugging And Validation

- Show CLI help: `python main.py --help`.
- Print the final JSON config produced from `boards/<board>/config.jsonnet`: `python main.py -b <board> -a <adapter> --skipbuild --skipimage --debug`.
- Run build stage only: `python main.py -b <board> -a <adapter> --skipimage`.
- Run image stage only: `python main.py -b <board> -a <adapter> --skipbuild`.
- Check `logs/<board>/`, `outputs/<board>/`, and `build/<board>/` when diagnosing failures.

## Ask Before Acting

Ask the developer before making changes when:

- The board or adapter is ambiguous.
- Required boot, partition, toolchain, firmware, artifact, or deployment details are missing.
- The requested behavior cannot be expressed with existing config, scripts, or actions.
- A full build or image generation may be needed.
- Existing files conflict and repository facts are insufficient to choose safely.
