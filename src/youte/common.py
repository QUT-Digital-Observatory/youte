from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional


@dataclass
class Resources:
    items: list

    def to_json(self, filepath: Path | str, pretty: bool = False) -> None:
        json_array: list = []
        indent: Optional[int] = 4 if pretty else None
        for item in self.items:
            json_array.append(asdict(item))
            with open(filepath, mode="w", encoding="utf-8") as f:
                f.write(
                    json.dumps(
                        json_array, default=str, indent=indent, ensure_ascii=False
                    )
                )

    def to_csv(self, filepath: Path | str, encoding: str = "utf-8") -> None:
        with open(filepath, "w", newline="", encoding=encoding) as csvfile:
            fieldnames = asdict(self.items[0]).keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for item in self.items:
                writer.writerow(asdict(item))
