from pathlib import Path

from process import shell


async def run(action: dict, cwd: Path, env: dict[str, str]) -> None:
    src = action["src"]
    path = action.get("path", ".")
    branch = action.get("branch")
    commit_hash = action.get("hash")

    cmd = "git clone"
    if not commit_hash:
        cmd += " --depth=1"
    if branch:
        cmd += f" -b {branch}"
    cmd += f" {src} {path}"
    await shell(cmd, cwd=cwd, env=env)

    if commit_hash:
        repo_dir = cwd / path
        await shell(f"git checkout {commit_hash}", cwd=repo_dir, env=env)
