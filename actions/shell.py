from collections.abc import Sequence
from pathlib import Path

from pydantic import Field

from actions.base import BaseAction
from process import shell


class Action(BaseAction):
    cmds: Sequence[str] = Field(default_factory=tuple)

    async def run(self, cwd: Path, env: dict[str, str]) -> None:
        for cmd in self.cmds:
            await shell(cmd, cwd, env)
