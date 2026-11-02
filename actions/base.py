from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, computed_field

if TYPE_CHECKING:
    PathArg = Path | str
else:
    PathArg = Path


class BaseAction(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    @computed_field
    @property
    def use(self) -> str:
        return self.__class__.__module__.rsplit(".", 1)[-1]

    async def run(self, cwd: Path, env: dict[str, str]) -> None:
        raise NotImplementedError
