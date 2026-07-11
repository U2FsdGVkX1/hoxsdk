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
    debug: list[DebugConfig]
    params_raw: list[tuple[str, str]]
    params: dict[str, str]


def parse_debug(value: str) -> DebugConfig:
    module_name, _, action_index = value.partition(":")
    if not action_index:
        action_index = "*"
    return DebugConfig(module_name, action_index)


def parse_param(value: str) -> tuple[str, str]:
    key, sep, val = value.partition(":")
    return key, val if sep else "true"


def parse_arguments() -> Args:
    parser = argparse.ArgumentParser(fromfile_prefix_chars="@")
    parser.add_argument("-b", "--board", type=str, required=True, help="Board name")
    parser.add_argument("-a", "--adapter", type=str, required=True, help="Image adapter name")
    parser.add_argument("--desktop", type=str, default="minimal", help="Desktop profile name")
    parser.add_argument("--skipbuild", action="store_true", help="Skip build stage")
    parser.add_argument("--skipimage", action="store_true", help="Skip image stage")
    parser.add_argument(
        "--debug",
        action="append",
        nargs="?",
        const="*",
        default=[],
        type=parse_debug,
        metavar="MODULE[:INDEX]",
        help=(
            "Print parsed config and pause before matched build actions; "
            "default when given without a value: *. Repeatable to combine "
            "multiple patterns (e.g. --debug 'kernel:*' --debug 'uboot:1')."
        ),
    )
    parser.add_argument(
        "-p",
        "--param",
        dest="params_raw",
        action="append",
        default=[],
        metavar="KEY[:VALUE]",
        type=parse_param,
        help=(
            "Set a parameter as KEY:VALUE (or just KEY as shorthand for "
            "KEY:true). Parameters are available to the build and image "
            "stages; repeatable."
        ),
    )

    args = parser.parse_args(namespace=Args())
    args.params = dict(args.params_raw)
    return args


async def main(args: Args) -> None:
    root = Path(__file__).resolve().parent
    boarddir = (root / "boards" / args.board).resolve()
    adapterdir = (root / "adapters" / args.adapter).resolve()
    builddir = (root / "build" / args.board).resolve()
    outputdir = (root / "outputs" / args.board).resolve()
    logdir = (root / "logs" / args.board).resolve()
    builddir.mkdir(parents=True, exist_ok=True)
    outputdir.mkdir(parents=True, exist_ok=True)

    config_ns = runpy.run_path(str(boarddir / "config.py"))
    config = config_ns["configure"](
        ConfigContext(
            BOARD_NAME=boarddir.name,
            BOARD_DIR=boarddir,
            ADAPTER_NAME=args.adapter,
            ADAPTER_DIR=adapterdir,
            PARAMS=args.params,
        )
    )
    manager = Manager(
        config=config,
        boarddir=boarddir,
        adapterdir=adapterdir,
        builddir=builddir,
        outputdir=outputdir,
        logdir=logdir,
        debug=args.debug,
        params=args.params,
    )
    if args.debug:
        print(manager.config.model_dump(
            mode="json", by_alias=True, serialize_as_any=True
        ))

    if not args.skipbuild:
        await manager.build()

    if not args.skipimage:
        await manager.images()
        print(f"[image] Generated outputs in: {outputdir}")


if __name__ == "__main__":
    asyncio.run(main(parse_arguments()))
