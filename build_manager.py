import asyncio
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

from sdkhelper import Target


@dataclass(frozen=True)
class DebugConfig:
    target_name: str
    action_index: str

    def matches(self, target_name: str, action_index: int) -> bool:
        matches_target = self.target_name == "*" or self.target_name == target_name
        matches_action = self.action_index == "*" or self.action_index == str(action_index)
        return matches_target and matches_action

class BuildManager:
    def __init__(
        self,
        targets: Dict,
        builddir: Path,
        outputdir: Path,
        debug: list[DebugConfig] = [],
    ):
        self.targets: dict[str, Target] = {
            name: Target(target_config)
            for name, target_config in targets.items()
        }
        self.builddir = builddir.resolve()
        self.outputdir = outputdir.resolve()
        self.debug: list[DebugConfig] = debug
        self.running_tasks: dict[str, asyncio.Task] = {}

    def _load_env_file(self, env_file: Path) -> dict[str, str]:
        env_extension: dict[str, str] = {}
        if not env_file.exists():
            return env_extension

        with env_file.open("r") as file:
            for line in file:
                line = line.strip()
                if not line or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                env_extension[key] = value

        return env_extension

    async def _open_debug_shell(
        self,
        target_name: str,
        action_index: int,
        action_name: str,
        cwd: Path,
        env: dict[str, str],
    ) -> None:
        print(f"[debug] Paused before {target_name}:{action_index} ({action_name})")
        print(f"[debug] cwd: {cwd}")
        print("[debug] Exit the shell to continue")

        process = await asyncio.create_subprocess_exec(
            os.environ.get("SHELL") or "/bin/bash",
            cwd=cwd,
            env={**os.environ, **env},
        )
        await process.wait()

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

        for action_index, action in enumerate(target.actions):
            env_file = actiondir / ".env"
            env_extension = self._load_env_file(env_file)
            if any(
                item.matches(target_name, action_index)
                for item in self.debug
            ):
                await self._open_debug_shell(
                    target_name,
                    action_index,
                    action.__class__.__name__,
                    actiondir,
                    {**target.env, **env_extension},
                )
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
