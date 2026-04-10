import asyncio
import argparse
import json
import _jsonnet
from pathlib import Path

from build_manager import BuildManager
from image_manager import ImageManager


class Args(argparse.Namespace):
    board: str
    adapter: str
    desktop: str
    skipbuild: bool
    skipimage: bool


def parse_arguments() -> Args:
    parser = argparse.ArgumentParser()
    parser.add_argument("-b", "--board", type=str, required=True, help="Board name")
    parser.add_argument("-a", "--adapter", type=str, required=True, help="Image adapter name")
    parser.add_argument("--desktop", type=str, default="minimal", help="Desktop profile name")
    parser.add_argument("--skipbuild", action="store_true", help="Skip build stage")
    parser.add_argument("--skipimage", action="store_true", help="Skip image stage")
    return parser.parse_args(namespace=Args())


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

    # build
    if not args.skipbuild:
        build_manager = BuildManager(
            config.get("targets", {}),
            builddir,
            outputdir,
        )
        await build_manager.build()

    # image
    if not args.skipimage:
        adapterdir = (root / "adapters" / args.adapter).resolve()
        image_manager = ImageManager(
            config["arch"],
            args.desktop,
            config.get("partitions", []),
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
