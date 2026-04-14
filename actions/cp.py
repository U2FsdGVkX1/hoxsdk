import shutil
from pathlib import Path


async def run(action: dict, cwd: Path, env: dict[str, str]) -> None:
    src = cwd / action["src"]
    dst = cwd / action["dest"]
    if src.is_dir():
        shutil.copytree(src, dst, dirs_exist_ok=True)
    else:
        shutil.copy2(src, dst)
