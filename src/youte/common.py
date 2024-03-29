from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel


class YouteClass(BaseModel):
    class Config:
        orm_mode = True


@dataclass
class Resources:
    items: list[YouteClass]

    def add(self, *args):
        for other in args:
            if isinstance(other, self.__class__):
                self.items.extend(other.items)
            else:
                raise TypeError(f"Objected added must be class {self.__class__}")

    def to_json(self, filepath: Path | str, pretty: bool = False) -> None:
        json_array: list = []
        indent: Optional[int] = 4 if pretty else None
        for item in self.items:
            json_array.append(_flatten_json(dict(item)))
            with open(filepath, mode="w", encoding="utf-8") as f:
                f.write(
                    json.dumps(
                        json_array, default=str, indent=indent, ensure_ascii=False
                    )
                )

    def to_csv(self, filepath: Path | str, encoding: str = "utf-8-sig") -> None:
        with open(filepath, "w", newline="", encoding=encoding) as csvfile:
            fieldnames = _flatten_json(dict(self.items[0])).keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for item in self.items:
                writer.writerow(_flatten_json(dict(item)))


def _flatten_json(obj: dict[str, Any]) -> dict[str, Any]:
    out = {}

    def flatten(x: str | dict | list, name: str = ""):
        if type(x) is dict:
            for a in x:
                flatten(x[a], name + a + "_")
        else:
            out[name[:-1]] = x

    flatten(obj)
    return out
