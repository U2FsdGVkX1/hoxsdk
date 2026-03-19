from pathlib import Path
from dataclasses import dataclass, field
from fmhelper import Action, shell

@dataclass
class PatchAction(Action):
    patches: list = field(default_factory=list)
    gitam: bool = False
    async def run(self, cwd: Path, env: dict) -> None:
        for patch in self.patches:
            if self.gitam:
                process, _, stderr = await shell(f"git am {patch}", cwd=cwd, env=env)
                if process.returncode != 0:
                    raise RuntimeError(f"git am failed for {patch}:\n{stderr.decode()}")
            else:
                process, _, stderr = await shell(f"patch -p1 < {patch}", cwd=cwd, env=env)
                if process.returncode != 0:
                    raise RuntimeError(f"patch failed for {patch}:\n{stderr.decode()}")