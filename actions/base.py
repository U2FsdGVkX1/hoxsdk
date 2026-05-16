from pathlib import Path

from pydantic import BaseModel, ConfigDict, computed_field


class BaseAction(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    @computed_field
    @property
    def use(self) -> str:
        return self.__class__.__module__.rsplit(".", 1)[-1]

    async def run(self, cwd: Path, env: dict[str, str]) -> None:
        raise NotImplementedError
