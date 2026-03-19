from pathlib import Path
from dataclasses import dataclass, field
from fmhelper import Action, shell

@dataclass
class ShellAction(Action):
    cmds: list = field(default_factory=list)
    async def run(self, cwd: Path, env: dict) -> None:
        for cmd in self.cmds:
            process, _, stderr = await shell(cmd, cwd, env)
            if process.returncode != 0:
                raise RuntimeError(f"Shell command failed: {cmd}\n{stderr.decode()}")