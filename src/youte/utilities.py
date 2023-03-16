from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Iterable, Iterator, Literal, Optional, Union

import click

from youte._typing import APIResponse
from youte.exceptions import InvalidFileName

logger = logging.getLogger(__name__)

_VALID_OUTPUT = ("json", "jsonl")


def validate_file(file_name: str, suffix=None):
    path = Path(file_name)
    if suffix and path.suffix != suffix:
        raise InvalidFileName("File name must end in `%s`." % suffix)
    return path


def check_file_overwrite(file_path: Path) -> Path:
    if file_path.exists():
        flag = click.confirm(f"{file_path} already exists. Keep writing to it?")
        if flag:
            logger.info(f"Updating existing file {file_path.resolve()}...")
        else:
            file_name = input("Input new file name: ")
            file_path = Path(file_name)

    return file_path


def create_utc_datetime_string(string: Optional[str] = None) -> Union[str, None]:
    return f"{string}T00:00:00Z" if string else None


def validate_date_string(string: str) -> bool:
    pattern = r"^([0-9]{4})-(1[0-2]|0[1-9])-(3[01]|0[1-9]|[12][0-9])$"
    if re.match(pattern, string):
        return True
    else:
        return False


def export_file(
    obj: Iterable[APIResponse],
    fp: str | Path,
    file_format: Literal["json", "jsonl"],
    pretty: bool = False,
    ensure_ascii=True,
) -> None:
    if file_format not in _VALID_OUTPUT:
        raise ValueError(f"file_format has to be one of {_VALID_OUTPUT}")

    indent: Optional[int] = 4 if pretty else None

    if file_format == "json":
        json_arrays: list[dict] = [json_obj for json_obj in obj]
        with open(fp, "w") as file:
            file.write(
                json.dumps(
                    json_arrays, default=str, indent=indent, ensure_ascii=ensure_ascii
                )
            )

    if file_format == "jsonl":
        with open(fp, "w") as file:
            for json_obj in obj:
                file.write(
                    json.dumps(json_obj, default=str, ensure_ascii=ensure_ascii) + "\n"
                )


def retrieve_ids_from_file(filepath: str | Path) -> Iterator[str]:
    """Utility function to retrieve just the IDs from API JSON response.
    The file specified has to be raw JSON data from YouTube API, not
    parsed JSON using youte parser.
    """
    items = _get_items(filepath)
    yield from _get_id(items)


def _get_items(filepath: str | Path) -> Iterator[dict]:
    """Utility function to get each item from raw API JSON response"""
    filepath = Path(filepath) if isinstance(filepath, str) else filepath
    with open(filepath, mode="r") as file:
        if filepath.suffix == ".jsonl":
            responses = (row.strip() for row in file.readlines())
            for response in responses:
                try:
                    items = json.loads(response)["items"]
                    for item in items:
                        yield item
                except KeyError:
                    logger.warning("No items found in JSON response")
        elif filepath.suffix == ".json":
            responses = json.loads(file.read())
            for response in responses:
                try:
                    items = response["items"]
                    for item in items:
                        yield item
                except KeyError:
                    logger.warning("No items found in JSON response")


def _get_id(items: Iterable[dict]) -> Iterator[str]:
    for item in items:
        id_ = item["id"]
        if isinstance(id_, dict):
            for elem in id_:
                if "id" in elem or "Id" in elem:
                    id_ = id_[elem]
        yield id_
