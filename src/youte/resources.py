import json
from pathlib import Path
from typing import Union

_VALID_OUTPUT = ["csv", "json", "jsonl"]


class SearchResource:
    def __init__(self, params: dict, response: dict):
        self.params = params
        self.json = response
        self.text = json.dumps(response)

    def write(self, output: Union[str, Path], output_format: str):
        if output_format not in _VALID_OUTPUT:
            raise ValueError(f"Format {output_format} not one of {_VALID_OUTPUT}.")
