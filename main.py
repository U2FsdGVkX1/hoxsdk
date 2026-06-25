import asyncio
import argparse
import runpy
from pathlib import Path

from hox import ConfigContext
from manager import DebugConfig, Manager


class Args(argparse.Namespace):
    board: str
    adapter: str
    desktop: str
    skipbuild: bool
    skipimage: bool
    debug_raw: str
    debug: list[DebugConfig]


def parse_debug(value: str) -> list[DebugConfig]:
    items = []
    for part in value.split(","):
        if not part:
            continue

        module_name, _, action_index = part.partition(":")
        if not action_index:
            action_index = "*"

        items.append(DebugConfig(module_name, action_index))
    return items


def parse_arguments() -> Args:
    parser = argparse.ArgumentParser(fromfile_prefix_chars="@")
    parser.add_argument("-b", "--board", type=str, required=True, help="Board name")
    parser.add_argument("-a", "--adapter", type=str, required=True, help="Image adapter name")
    parser.add_argument("--desktop", type=str, default="minimal", help="Desktop profile name")
    parser.add_argument("--skipbuild", action="store_true", help="Skip build stage")
    parser.add_argument("--skipimage", action="store_true", help="Skip image stage")
    parser.add_argument(
        "--debug",
        dest="debug_raw",
        nargs="?",
        const="*",
        type=str,
        default="",
        metavar="MODULE[:INDEX][,...]",
        help=(
            "Print parsed config and pause before matched build actions; "
            "default: *"
        ),
    )

    args = parser.parse_args(namespace=Args())
    args.debug = parse_debug(args.debug_raw)
    return args


async def main():
    root = Path(__file__).resolve().parent
    boarddir = (root / "boards" / args.board).resolve()
    adapterdir = (root / "adapters" / args.adapter).resolve()
    builddir = (root / "build" / args.board).resolve()
    outputdir = (root / "outputs" / args.board).resolve()
    builddir.mkdir(parents=True, exist_ok=True)
    outputdir.mkdir(parents=True, exist_ok=True)

    config_ns = runpy.run_path(str(boarddir / "config.py"))
    config = config_ns["configure"](
        ConfigContext(
            BOARD_NAME=boarddir.name,
            BOARD_DIR=boarddir,
            ADAPTER_NAME=args.adapter,
            ADAPTER_DIR=adapterdir,
        )
    )
    manager = Manager(
        config,
        boarddir,
        adapterdir,
        builddir,
        outputdir,
        args.debug,
    )
    if args.debug:
        print(manager.config.model_dump(
            mode="json", by_alias=True, serialize_as_any=True
        ))

    if not args.skipbuild:
        await manager.build()

    if not args.skipimage:
        # process.shell() routes logs by the current task name; naming this
        # task routes all image-stage output to logs/<board>/_image.log
        # instead of the module build logs.
        await asyncio.create_task(manager.images(), name="_image")
        print(f"[image] Generated outputs in: {outputdir}")

args = parse_arguments()
if __name__ == "__main__":
    asyncio.run(main())
