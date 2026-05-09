import asyncio
import importlib
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    RootModel,
    field_validator,
    model_validator,
)

from actions.base import BaseAction


@dataclass(frozen=True)
class DebugConfig:
    target_name: str
    action_index: str

    def matches(self, target_name: str, action_index: int) -> bool:
        matches_target = self.target_name == "*" or self.target_name == target_name
        matches_action = self.action_index == "*" or self.action_index == str(action_index)
        return matches_target and matches_action


class Target(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    requires: tuple[str, ...] = Field(default_factory=tuple)
    depends: tuple[str, ...] = Field(default_factory=tuple)
    env: dict[str, str] = Field(default_factory=dict)
    actions: tuple[BaseAction, ...] = Field(default_factory=tuple)
    result: tuple[str, ...] = Field(default_factory=tuple)

    @field_validator("actions", mode="before")
    @classmethod
    def validate_actions(cls, actions: Any) -> tuple[BaseAction, ...]:
        if actions is None:
            return tuple()

        loaded_actions: list[BaseAction] = []
        for action_config in actions:
            if not isinstance(action_config, dict):
                raise ValueError("Action config must be a dict")

            use = action_config.get("use")
            if not isinstance(use, str) or not use:
                raise ValueError("Action config must include non-empty string 'use'")

            module_name = f"actions.{use}"
            try:
                module = importlib.import_module(module_name)
            except ModuleNotFoundError as exc:
                if exc.name == module_name:
                    raise ValueError(f"Unknown action '{use}'") from exc
                raise

            action_type = getattr(module, "Action", None)
            if not action_type:
                raise ValueError(f"Action '{use}' must export Action inheriting BaseAction")
            if not issubclass(action_type, BaseAction):
                raise ValueError(
                    f"Action '{use}' must export Action inheriting BaseAction"
                )
            loaded_actions.append(action_type.model_validate(action_config))

        return tuple(loaded_actions)


class TargetGraph(RootModel[dict[str, Target]]):
    model_config = ConfigDict(frozen=True)

    @model_validator(mode="after")
    def validate_dependencies(self) -> "TargetGraph":
        for name, target in self.root.items():
            for depend in target.depends:
                if depend not in self.root:
                    raise ValueError(
                        f"Target '{name}' depends on unknown target '{depend}'"
                    )

        visiting: set[str] = set()
        visited: set[str] = set()
        stack: list[str] = []

        def visit(name: str) -> list[str] | None:
            if name in visited:
                return None
            if name in visiting:
                return stack[stack.index(name):] + [name]

            visiting.add(name)
            stack.append(name)
            for depend in self.root[name].depends:
                cycle = visit(depend)
                if cycle:
                    return cycle
            stack.pop()
            visiting.remove(name)
            visited.add(name)
            return None

        for name in self.root:
            cycle = visit(name)
            if cycle:
                raise ValueError(f"Dependency cycle detected: {' -> '.join(cycle)}")

        return self


class BuildManager:
    def __init__(
        self,
        targets: dict[str, dict[str, Any]],
        builddir: Path,
        outputdir: Path,
        debug: list[DebugConfig] | None = None,
    ):
        self.targets = TargetGraph.model_validate(targets).root
        self.builddir = builddir.resolve()
        self.outputdir = outputdir.resolve()
        self.debug = tuple(debug or [])
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
            env_extension = self._load_env_file(actiondir / ".env")
            env = {**target.env, **env_extension}
            if any(
                item.matches(target_name, action_index)
                for item in self.debug
            ):
                await self._open_debug_shell(
                    target_name,
                    action_index,
                    action.use,
                    actiondir,
                    env,
                )
            await action.run(actiondir, env)

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
