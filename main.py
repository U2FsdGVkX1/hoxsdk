import asyncio
import argparse
import yaml
import shutil
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from typing import Dict, Optional
from fmhelper import Target

class BuildManager:
    name: str
    config: Dict
    targets: Dict[str, Target] = {}
    running_tasks: Dict[str, asyncio.Task] = {}

    def __init__(self, name: str, config: Dict):
        self.name = name
        self.config = config
        for name, target in self.config.items():
            self.targets[name] = Target(target)

    async def build_target(self, target_name: str, workdir: Path) -> Path:
        target = self.targets[target_name]

        for require in target.requires:
            if not shutil.which(require):
                raise EnvironmentError(f"Required tool '{require}' not found in PATH")

        for depend in target.depends:
            await self.running_tasks[depend]

        actiondir = workdir / target_name
        if actiondir.exists():
            shutil.rmtree(actiondir)
        actiondir.mkdir(parents=True, exist_ok=True)

        for action in target.actions:
            env_extension: dict[str, str] = {}
            env_file = actiondir / ".env"
            if env_file.exists():
                with open(env_file, "r") as file:
                    for line in file:
                        line = line.strip()
                        if not line or '=' not in line:
                            continue
                        key, value = line.split("=", 1)
                        env_extension[key] = value
            await action.run(actiondir, {**target.env, **env_extension})
            print(f"[{target_name}] Built: {action.__class__.__name__}")

        for result in target.result:
            for matched_file in actiondir.glob(result):
                shutil.copy(matched_file, workdir)

        return actiondir
    
    async def execute_build_target(self, workdir: Path, target_filter: Optional[str] = None) -> Path:
        builddir = (workdir / self.name).resolve()
        builddir.mkdir(parents=True, exist_ok=True)

        for name, target in self.targets.items():
            if target_filter:
                if name not in ([target_filter] + target.depends):
                    continue
            self.running_tasks[name] = asyncio.create_task(
                self.build_target(name, builddir),
                name=f"{self.name}/{name}"
            )
        await asyncio.gather(*self.running_tasks.values())
        return builddir

async def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("-b", "--board", type=str, help="Board name")
    parser.add_argument("-t", "--target", type=str, help="Target to build")
    return parser.parse_args()

async def prepare_boardconfig(board_name: str) -> Dict:
    boarddir = Path(f"boards/{board_name}").resolve()
    root = Path(".").resolve()

    env = Environment(loader=FileSystemLoader('templates'))
    env.globals['ROOT'] = str(root)
    env.globals['BDIR'] = str(boarddir)

    values_file = boarddir / "values.yaml"
    if values_file.exists():
        with open(values_file, "r") as file:
            template = env.from_string(file.read())
            rendered_values = template.render()
            values: Dict = yaml.safe_load(rendered_values)
    else:
        values = {}

    config_file = boarddir / "config.yaml"
    with open(config_file, "r") as file:
        template = env.from_string(file.read())
        rendered_config = template.render(**values)
        config = yaml.safe_load(rendered_config)
    return config

async def main():
    args = await parse_arguments()
    if not args.board:
        print("Error: --board is required for build operations")
        return

    config = await prepare_boardconfig(args.board)
    manager = BuildManager(args.board.split("/")[-1], config)
    resultdir = await manager.execute_build_target(Path('build'), args.target)

if __name__ == "__main__":
    asyncio.run(main())
