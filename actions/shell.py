from pathlib import Path

from process import shell


async def run(action: dict, cwd: Path, env: dict[str, str]) -> None:
    for cmd in action.get("cmds", []):
        await shell(cmd, cwd, env)
