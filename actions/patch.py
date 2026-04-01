from pathlib import Path
from dataclasses import dataclass, field

from sdkhelper import Action, shell

@dataclass
class PatchAction(Action):
    patches: list = field(default_factory=list)
    gitam: bool = False
    async def run(self, cwd: Path, env: dict) -> None:
        for patch in self.patches:
            if self.gitam:
                await shell(f"git am {patch}", cwd=cwd, env=env)
            else:
                await shell(f"patch -p1 < {patch}", cwd=cwd, env=env)
