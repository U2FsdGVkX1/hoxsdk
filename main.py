import asyncio
import argparse
import json
import _jsonnet
from pathlib import Path

from build_manager import BuildManager, DebugConfig
from image_manager import ImageManager


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

        target_name, separator, action_index = part.partition(":")
        if not separator:
            action_index = "*"
        elif not action_index:
            action_index = "*"

        items.append(DebugConfig(target_name, action_index))
    return items


def parse_arguments() -> Args:
    parser = argparse.ArgumentParser()
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
        metavar="TARGET[:INDEX][,...]",
        help=(
            "Print parsed jsonnet config and pause before matched actions; "
            "default: *"
        ),
    )

    args = parser.parse_args(namespace=Args())
    args.debug = parse_debug(args.debug_raw)
    return args


async def main():
    # Determine root directory
    root = Path(__file__).resolve().parent

    # Validate directory
    boarddir = (root / "boards" / args.board).resolve()
    builddir = (root / "build" / args.board).resolve()
    outputdir = (root / "outputs" / args.board).resolve()
    builddir.mkdir(parents=True, exist_ok=True)
    outputdir.mkdir(parents=True, exist_ok=True)

    # Config
    content = _jsonnet.evaluate_file(
        str(boarddir / "config.jsonnet"),
        ext_vars={"BDIR": str(boarddir)},
    )
    config = json.loads(content)
    if args.debug:
        print(json.dumps(config, indent=2, ensure_ascii=False))

    # build
    if not args.skipbuild:
        build_manager = BuildManager(
            config.get("targets", {}),
            builddir,
            outputdir,
            args.debug,
        )
        await build_manager.build()

    # image
    if not args.skipimage:
        adapterdir = (root / "adapters" / args.adapter).resolve()
        image_manager = ImageManager(
            config["arch"],
            args.desktop,
            config.get("partitions", []),
            config.get("images", []),
            boarddir,
            adapterdir,
            builddir,
            outputdir,
        )
        await asyncio.create_task(image_manager.generate(), name="_image")
        print(f"[image] Generated outputs in: {outputdir}")

args = parse_arguments()
if __name__ == "__main__":
    asyncio.run(main())
