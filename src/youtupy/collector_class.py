import logging
import sqlite3
import requests
from datetime import datetime
from dateutil import tz
import random
import json
import time
from typing import Optional, Union, Any
from pathlib import Path

from youtupy.quota import Quota
from youtupy.utilities import (
    insert_ids_to_db,
    validate_file,
    check_file_overwrite,
    create_utc_datetime_string
)
from youtupy import databases
from youtupy.exceptions import InvalidRequestParameter, StopCollector
from youtupy.process import process_to_database

logger = logging.getLogger(__name__)


class SearchCollector():

    def __init__(self, api_key: str, max_quota: int = 10000):
        self.params = {
            'part': 'snippet',
            'maxResults': 50,
            'q': None,
            'type': 'video',
            'order': 'date',
            'safeSearch': 'none',
            'key': None
            }
        self.api_cost = 100
        self.url = 'https://www.googleapis.com/youtube/v3/search'
        self.output_path = None
        self.api_key = api_key
        self.max_quota = max_quota

    def add_param(self, **param: Union[str,float]) -> None:
        for key, value in param.items():
            if (key == 'publishedAfter' or
                    key == 'publishedBefore'):
                value = create_utc_datetime_string(value)
            self.params[key] = value

    def run(self, dbpath: str) -> None:

        # validate and set up database
        dbpath = validate_file(dbpath)

        if dbpath.exists():
            logger.info(f"Creating {dbpath} at {dbpath.resolve().parent}.")
            databases.initialise_database(path=dbpath)
        else:
            dbpath = check_file_overwrite(dbpath)

        self.output_path = dbpath
        db = sqlite3.connect(dbpath)
        databases.initialise_database(path=dbpath)

        # check that search requests have query
        if not self.params['q']:
            raise InvalidRequestParameter("Search query is required for "
                                          "search requests.")

        if ('publishedAfter' not in self.params and
                'publishedBefore' not in self.params):
            logger.warning("""
                No start date or end date is specified for this request.
                This might result in a large amount of data being requested,
                using up available quota. Do you want to continue [Y/N]?
                """)
            check = input("[Y/N]: ").lower()
            if check == 'n':
                raise StopCollector("Stopping the collector...")

        self.params['key'] = self.api_key

        quota = Quota(api_key=self.api_key)
        quota.get_quota()

        logger.info(
            f"""
            Starting querying Youtube search results. 
            Quota unit cost will be {self.api_cost}.
            """)

        while True:

            with db:
                # empty string for the base request url because it
                # doesn't have a page token
                db.execute(
                    """
                    INSERT OR IGNORE INTO search_api_response(next_page_token) 
                    VALUES ('')
                    """)

                # get list of unrecorded page tokens
                logger.info("Getting data from database.")

                to_retrieve = set(
                    row[0]
                    for row in db.execute(
                        """
                        SELECT next_page_token 
                        FROM search_api_response 
                        WHERE retrieval_time IS NULL
                        """)
                )

            if not len(to_retrieve):
                logger.info("END OF RESULT SET HAS BEEN REACHED.")
                break

            logger.debug("Handling limit...")
            quota.handle_limit(max_quota=self.max_quota)

            for token in to_retrieve:
                # if base url has not been requested yet, request base url

                if token == "":
                    r = requests.get(self.url, params=self.params)
                else:
                    self.params['pageToken'] = token
                    r = requests.get(self.url, params=self.params)

                quota.add_quota(unit_costs=self.api_cost,
                                created_utc=datetime.now(tz=tz.UTC))

                logger.info(
                    f"""
                     Getting requests ... {quota.units}/{self.max_quota} used.
                     Status: {r.status_code}
                     """)

                logger.debug(
                    f"""
                    {r.url}
                    {r.status_code}
                    """)

                r.raise_for_status()

                if r.status_code == 403:
                    print(r.json()['error']['message'])
                    break

                # get nextPageToken from current response
                # and insert it to the database

                try:
                    next_page_token = r.json()['nextPageToken']
                    db.execute(
                        """
                        INSERT OR IGNORE INTO 
                        search_api_response(next_page_token) 
                        VALUES (?)
                        """,
                        (next_page_token,))

                except KeyError as e:
                    logger.info(f"NO MORE RESULT PAGE TO PAGINATE...")

                # update database with response from current request

                db.execute(
                    """
                    REPLACE INTO search_api_response(next_page_token,
                                                       request_url,
                                                       status_code,
                                                       response,
                                                       total_results,
                                                       retrieval_time)
                    VALUES (?,?,?,?,?,?)
                    """,
                    (token, r.url, r.status_code, json.dumps(r.json()),
                     len(r.json()['items']),
                     datetime.utcnow())
                )

                time.sleep(random.uniform(3, 6))

        process_to_database(source='search', dbpath=dbpath)

        logger.info(
            f"""
            DATA COLLECTION COMPLETED.
            DATA IS STORED IN {dbpath} in location {dbpath.resolve().parent}.
                - RAW JSON IS STORED IN search_api_response SCHEMA.
                - CLEAN DATA IS STORED IN search_results SCHEMA.
            """
        )

    def get_enriching_data(self, endpoint: ['video', 'channel']):
        endpoint_url = _get_endpoint(endpoint)['url']
        endpoint_api_cost = _get_endpoint(endpoint)['api_cost_unit']
        endpoint_params = _get_endpoint(endpoint)['params']
        endpoint_params['key'] = self.api_key

        if not self.output_path:
            raise InvalidRequestParameter("No search results found. "
                                          "Do a Youtube search request first.")
        else:
            db = sqlite3.connect(self.output_path)

            insert_ids_to_db(self.output_path, source=endpoint)
            item_ids = [row[0]
                        for row in
                        db.execute(
                        f"""
                        SELECT {endpoint}_id 
                        FROM {endpoint}_api_response 
                        WHERE retrieval_time IS NULL 
                        LIMIT 50
                        """)]
            if not item_ids:
                logger.warning("""
                    No data found in Youtube search results.
                    Have you done a Youtube search? Check if your Youtube
                    search returned any data.
                    """)
            else:
                quota = Quota(api_key=self.api_key)
                quota.get_quota()

                while True:
                    item_ids = [row[0]
                                for row in
                                db.execute(
                                    f"""
                                   SELECT {endpoint}_id 
                                   FROM {endpoint}_api_response 
                                   WHERE retrieval_time IS NULL 
                                   LIMIT 50
                                   """)]

                    if item_ids:
                        endpoint_params['id'] = ','.join(item_ids)

                        logger.debug("Handling limit......")
                        quota.handle_limit(max_quota=self.max_quota)

                        response = requests.get(endpoint_url,
                                                params=endpoint_params)
                        logger.debug(f"Getting request {response.url}.")
                        response.raise_for_status()

                        logging.info(
                            f"""
                            Getting data from Youtube Video API... 
                            {quota.units}/{self.max_quota} used...
                            """)

                        quota.add_quota(unit_costs=endpoint_api_cost,
                                        created_utc=datetime.now(tz=tz.UTC))

                        logger.info(
                            f"Inserting data to {endpoint}_api_response")

                        with db:
                            try:
                                for i, item in enumerate(
                                        response.json()['items']):
                                    item_id = item['id']
                                    logger.debug(
                                        f"""
                                        Inserting {item_id}. {i + 1}/{len(
                                            response.json()['items'])}... 
                                        """)
                                    db.execute(
                                        f"""
                                        REPLACE INTO 
                                        {endpoint}_api_response({endpoint}_id, 
                                                           response, 
                                                           retrieval_time) 
                                        VALUES (?,?,?)
                                        """,
                                        (item_id, json.dumps(item),
                                         datetime.now(tz=tz.UTC))
                                    )
                            except KeyError:
                                logging.warning(
                                    f"""
                                    ONE OF THESE ITEMS COULD NOT BE FOUND:
                                    {','.join(item_ids)}.
                                    """)
                                for item_id in item_ids:
                                    db.execute(
                                        f"""
                                        REPLACE INTO 
                                        {endpoint}_api_response({endpoint}_id,
                                                            retrieval_time)
                                        VALUES (?,?)
                                        """,
                                        (item_id, datetime.now(tz=tz.UTC))
                                    )

                        time.sleep(random.uniform(3, 6))

                    else:
                        logger.warning("No more items in the result set.")
                        logger.info(f"""
                            RAW RESPONSES ARE IN {self.output_path},
                            SCHEMA: {endpoint}_api_response.
                            """)
                        break

                process_to_database(source=endpoint, dbpath=self.output_path)
                logger.info(
                    f"""
                    {endpoint.upper()} DATA COLLECTION COMPLETED.
                    DATA IS STORED IN {self.output_path} in location 
                        {Path(self.output_path).resolve().parent}.
                    - RAW JSON IS STORED IN {endpoint}_api_response SCHEMA.
                    - CLEAN DATA IS STORED IN {endpoint}_results SCHEMA.
                    """
                )


def _get_endpoint(endpoint: ['search', 'video', 'channel']) -> dict:
    """Get all the request details needed to make an API request to
    specified endpoints.

    Position argument:
        endpoint -- either 'search', 'video', or 'channel'
    """
    api_endpoints = {
        'search': {
            'url': r'https://www.googleapis.com/youtube/v3/search',
            'api_cost_unit': 100,
            'params': {
                'part': 'snippet',
                'maxResults': 50,
                'q': None,
                'type': 'video',
                'fields': 'pageInfo,prevPageToken,nextPageToken,'
                          'items(id, snippet(publishedAt, channelId, title,'
                          'description, channelTitle))',
                'order': 'date',
                'safeSearch': 'none',
                'key': None
            }
        },

        'video': {
            'url': r'https://www.googleapis.com/youtube/v3/videos',
            'api_cost_unit': 1,
            'params': {
                'part': 'snippet,statistics,topicDetails,status',
                'id': None,
                'maxResults': 50,
                'fields': 'nextPageToken,prevPageToken,'
                          'items(id,'
                          'snippet(publishedAt,channelId,title,description,'
                          'channelTitle),'
                          'status(uploadStatus),statistics,topicDetails)',
                'key': None
            }
        },

        'channel': {
            'url': r'https://www.googleapis.com/youtube/v3/channels',
            'api_cost_unit': 1,
            'params': {
                'part': 'snippet,statistics,topicDetails,status',
                'id': None,
                'maxResults': 50,
                'fields': 'nextPageToken,prevPageToken,'
                          'items(id,snippet(publishedAt,title,description),'
                          'status,statistics,topicDetails)',
                'key': None
            }
        }
    }

    return api_endpoints[endpoint]
