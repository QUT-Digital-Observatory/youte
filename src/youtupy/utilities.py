import sqlite3
import json
import logging
from pathlib import Path

from youtupy.exceptions import InvalidFileName

logger = logging.getLogger(__name__)


def insert_ids_to_db(dbpath, source: ['video', 'channel']):
    logger.debug("Connect to db...")
    db = sqlite3.connect(dbpath)

    source = source.lower()
    logger.debug("select response from api table")
    search_api_responses = db.execute(
        """
                SELECT response FROM search_api_response
                WHERE response NOTNULL
                """)

    item_ids = []

    logger.debug("extracting ids")
    for search_api_response in search_api_responses:
        items = json.loads(search_api_response[0])['items']
        for item in items:
            if source == 'video':
                item_id = item['id'][f'videoId']
            elif source == 'channel':
                item_id = item['snippet']['channelId']

            item_ids.append((item_id,))

    logger.debug("inserting ids")
    db.executemany(
        f"""
        INSERT OR IGNORE INTO {source}_api_response({source}_id) values(?) 
        """,
        item_ids)
    db.commit()
    db.close()


def validate_file(file_name, suffix=None):
    path = Path(file_name)
    if suffix and path.suffix != suffix:
        raise (InvalidFileName(f"File name must end in {suffix}."))
    return path


def check_file_overwrite(file_path: Path) -> Path:
    if file_path.exists():
        flag = input(
            """
            This database already exists. 
            Continue with this database? [Y/N]
            """).lower()

        if flag == 'y':
            logger.info(f"Updating existing database {file_path.resolve()}...")

        if flag == 'n':
            file_name = input("Input new database name: ")
            file_path = Path(file_name)

    return file_path


def create_utc_datetime_string(string: str):
    return f"{string}T00:00:00Z"