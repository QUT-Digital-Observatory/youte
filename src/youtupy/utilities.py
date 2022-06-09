import sqlite3
import json
import logging

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
