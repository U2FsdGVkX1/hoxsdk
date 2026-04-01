from pathlib import Path
from dataclasses import dataclass, field

from sdkhelper import Action, shell

@dataclass
class ShellAction(Action):
    cmds: list = field(default_factory=list)
    async def run(self, cwd: Path, env: dict) -> None:
        for cmd in self.cmds:
            await shell(cmd, cwd, env)
