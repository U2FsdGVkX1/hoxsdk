import asyncio
import shutil
from pathlib import Path
from typing import Dict

from sdkhelper import Target


class BuildManager:
    def __init__(self, targets: Dict, builddir: Path, outputdir: Path):
        self.builddir = builddir.resolve()
        self.outputdir = outputdir.resolve()
        self.targets: dict[str, Target] = {
            name: Target(target_config)
            for name, target_config in targets.items()
        }
        self.running_tasks: dict[str, asyncio.Task] = {}

    async def build_target(self, target_name: str) -> Path:
        target = self.targets[target_name]

        for require in target.requires:
            if not shutil.which(require):
                raise EnvironmentError(f"Required tool '{require}' not found in PATH")

        for depend in target.depends:
            await self.running_tasks[depend]

        actiondir = self.builddir / target_name
        if actiondir.exists():
            shutil.rmtree(actiondir)
        actiondir.mkdir(parents=True, exist_ok=True)

        for action in target.actions:
            env_extension: dict[str, str] = {}
            env_file = actiondir / ".env"
            if env_file.exists():
                with env_file.open("r") as file:
                    for line in file:
                        line = line.strip()
                        if not line or "=" not in line:
                            continue
                        key, value = line.split("=", 1)
                        env_extension[key] = value

            await action.run(actiondir, {**target.env, **env_extension})
            print(f"[{target_name}] Built: {action.__class__.__name__}")
        for result in target.result:
            for matched_file in actiondir.glob(result):
                shutil.move(matched_file, self.outputdir / matched_file.name)
        return actiondir

    async def build(self):
        for name in self.targets:
            self.running_tasks[name] = asyncio.create_task(
                self.build_target(name),
                name=name,
            )
        if self.running_tasks:
            await asyncio.gather(*self.running_tasks.values())
