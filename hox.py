import shutil
from collections.abc import Sequence
from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    SerializeAsAny,
    model_validator,
)

from actions.base import BaseAction


class Board(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    arch: str = Field(min_length=1)
    modules: Sequence[Module] = Field(default_factory=tuple)
    partitions: Sequence[Partition] = Field(default_factory=tuple)
    images: Sequence[Image] = Field(default_factory=tuple)

    @model_validator(mode="after")
    def validate_names(self) -> "Board":
        module_names = [module.name for module in self.modules]
        if len(module_names) != len(set(module_names)):
            raise ValueError("Module names must be unique")

        partition_names = [partition.name for partition in self.partitions]
        if len(partition_names) != len(set(partition_names)):
            raise ValueError("Partition names must be unique")

        image_names = [image.name for image in self.images]
        if len(image_names) != len(set(image_names)):
            raise ValueError("Image names must be unique")

        mountpoints = [partition.mountpoint for partition in self.partitions]
        if len(mountpoints) != len(set(mountpoints)):
            raise ValueError("Partition mountpoints must be unique")

        module_set = set(module_names)
        for module in self.modules:
            for field in (
                "build_after",
                "build_before",
                "install_after",
                "install_before",
            ):
                for dep in getattr(module, field):
                    if dep not in module_set:
                        raise ValueError(
                            f"Module '{module.name}' {field} references unknown module '{dep}'"
                        )

        return self


class Module(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(pattern=r"^[A-Za-z0-9_.-]+$")
    build_after: Sequence[str] = Field(default_factory=tuple)
    build_before: Sequence[str] = Field(default_factory=tuple)
    install_after: Sequence[str] = Field(default_factory=tuple)
    install_before: Sequence[str] = Field(default_factory=tuple)
    requires: Sequence[str] = Field(default_factory=tuple)
    env: dict[str, str] = Field(default_factory=dict)
    build: Sequence[SerializeAsAny[BaseAction]] = Field(default_factory=tuple)
    install: Sequence[str | Path] = Field(default_factory=tuple)

    @model_validator(mode="after")
    def validate_requires(self) -> "Module":
        for require in self.requires:
            if not shutil.which(require):
                raise ValueError(
                    f"Required tool '{require}' for module '{self.name}' not found in PATH"
                )
        return self


class Partition(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str
    size: int = Field(gt=0)
    mountpoint: str = Field(min_length=1)
    mkfs: str = Field(min_length=1)


class Image(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str
    table: Literal["gpt", "dos"] = "gpt"
    partitions: Sequence[ImagePartition]


class ImagePartition(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str
    start: int = Field(ge=0)
    size: int | None = Field(default=None, gt=0)
    type: str | None = None
    bootable: bool = False


@dataclass(frozen=True)
class ConfigContext:
    BOARD_NAME: str
    BOARD_DIR: Path
    ADAPTER_NAME: str
    ADAPTER_DIR: Path

    @property
    def adapter(self) -> list[Module]:
        return list(import_module(f"adapters.{self.ADAPTER_NAME}.config").configure(self))
