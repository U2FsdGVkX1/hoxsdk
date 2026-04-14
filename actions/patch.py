from pathlib import Path

from process import shell


async def run(action: dict, cwd: Path, env: dict[str, str]) -> None:
    for patch in action.get("patches", []):
        if action.get("gitam", False):
            await shell(f"git am {patch}", cwd=cwd, env=env)
        else:
            await shell(f"patch -p1 < {patch}", cwd=cwd, env=env)
