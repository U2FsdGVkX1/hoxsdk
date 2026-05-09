from pathlib import Path

from pydantic import BaseModel, ConfigDict


class BaseAction(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    use: str

    async def run(self, cwd: Path, env: dict[str, str]) -> None:
        raise NotImplementedError
