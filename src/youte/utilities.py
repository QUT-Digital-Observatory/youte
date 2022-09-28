import logging
from pathlib import Path
import click

from youte.exceptions import InvalidFileName

logger = logging.getLogger(__name__)


def validate_file(file_name, suffix=None):
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


def create_utc_datetime_string(string: str):
    return f"{string}T00:00:00Z"
