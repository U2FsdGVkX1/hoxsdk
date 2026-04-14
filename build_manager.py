import asyncio
import importlib
import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Target:
    requires: list[str] = field(default_factory=list)
    depends: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    actions: list[dict[str, Any]] = field(default_factory=list)
    result: list[str] = field(default_factory=list)


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
        targets: dict[str, dict[str, Any]],
        builddir: Path,
        outputdir: Path,
        debug: list[DebugConfig] = [],
    ):
        self.targets: dict[str, Target] = {
            name: Target(
                requires=target_config.get("requires", []),
                depends=target_config.get("depends", []),
                env=target_config.get("env", {}),
                actions=target_config.get("actions", []),
                result=target_config.get("result", []),
            )
            for name, target_config in targets.items()
        }
        self.builddir = builddir.resolve()
        self.outputdir = outputdir.resolve()
        self.debug = debug
        self.running_tasks: dict[str, asyncio.Task[Path]] = {}
    
    def _ensure_task(self, target_name: str) -> asyncio.Task[Path]:
        if target_name not in self.targets:
            raise ValueError(f"Unknown target '{target_name}'")
        if target_name not in self.running_tasks:
            self.running_tasks[target_name] = asyncio.create_task(
                self.build_target(target_name),
                name=target_name,
            )
        return self.running_tasks[target_name]

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
        await asyncio.gather(*(self._ensure_task(depend) for depend in target.depends))

        actiondir = self.builddir / target_name
        if actiondir.exists():
            shutil.rmtree(actiondir)
        actiondir.mkdir(parents=True, exist_ok=True)
        for action_index, action in enumerate(target.actions):
            use: str = action["use"]
            env_extension = self._load_env_file(actiondir / ".env")
            if any(
                item.matches(target_name, action_index)
                for item in self.debug
            ):
                await self._open_debug_shell(
                    target_name,
                    action_index,
                    use,
                    actiondir,
                    {**target.env, **env_extension},
                )

            module = importlib.import_module(f"actions.{use}")
            runner = getattr(module, "run", None)
            if runner is None:
                raise ValueError(f"Action '{use}' must export run()")
            await runner(action, actiondir, {**target.env, **env_extension})

        for result in target.result:
            for matched_file in actiondir.glob(result):
                shutil.move(matched_file, self.outputdir / matched_file.name)
        return actiondir

    async def build(self):
        if self.running_tasks:
            await asyncio.gather(*self.running_tasks.values())
            return
        if self.debug:
            for name in self.targets:
                await self._ensure_task(name)
        else:
            await asyncio.gather(*(self._ensure_task(name) for name in self.targets))
