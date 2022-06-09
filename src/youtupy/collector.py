import os
import logging
import sqlite3
import requests
from datetime import datetime
from dateutil import tz
import random
import json
import time

from quota import Quota
import utilities

logger = logging.getLogger(__name__)


def get_endpoint(endpoint: ['search', 'video', 'channel']) -> dict:
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
                'key': os.environ['YOUTUBE_API_KEY']
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
                'key': os.environ['YOUTUBE_API_KEY']
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
                'key': os.environ['YOUTUBE_API_KEY']
            }
        }
    }

    return api_endpoints[endpoint]


def collect(endpoint: ['search', 'video', 'channel'],
            dbpath: str, max_quota=10000, **query):
    """Collect data from Youtube API.

    Keyword arguments:
        endpoint -- either 'search', 'video', or 'channel'
        dbpath -- the path of the database (relative or absolute)
        max_quota -- default 10,000
        **query: any extra parameters passed to the 'search' request.
            Name of the parameter corresponds to the accepted fields
            specified in YouTube API.
    """
    # Set up request metadata and quota
    endpoint_meta = get_endpoint(endpoint)
    url = endpoint_meta['url']
    params = endpoint_meta['params']
    api_cost_unit = endpoint_meta['api_cost_unit']

    quota = Quota(api_key=os.environ['YOUTUBE_API_KEY'])
    quota.get_quota()

    db = sqlite3.connect(dbpath)

    logger.info(
        f"""
            Starting querying Youtube {endpoint} results. 
            Quota unit cost will be {api_cost_unit}.
            """)

    if endpoint == 'search':
        # SEARCH ENDPOINT
        params['q'] = query['q']

        if 'publishedAfter' in query:
            params['publishedAfter'] = f"{query['publishedAfter']}T00:00:00Z"
        if 'publishedBefore' in query:
            params['publishedBefore'] = f"{query['publishedAfter']}" \
                                        f"T00:00:00Z"

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
                logger.info("No more data to query.")
                break

            logger.debug("Handling limit...")
            quota.handle_limit(max_quota=max_quota)

            for token in to_retrieve:
                # if base url has not been requested yet, request base url

                if token == "":
                    r = requests.get(url, params=params)
                else:
                    params['pageToken'] = token
                    r = requests.get(url, params=params)

                quota.add_quota(unit_costs=api_cost_unit,
                                created_utc=datetime.now(tz=tz.UTC))

                logger.info(
                    f"""
                     Getting requests {r.url}. {quota.units}/{max_quota} used.
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
                    logger.warning(f"{e}. No more page to paginate...")

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

    elif endpoint == 'video' or endpoint == 'channel':
        # VIDEO AND CHANNEL ENDPOINTS

        # YouTube API accepts a list of up to 50 ids,
        # so this script makes several requests,
        # each searching for 50 items
        logger.info(f"Getting {endpoint} data...")

        logger.debug("Running insert ids...")

        utilities.insert_ids_to_db(dbpath, source=endpoint)

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
                params['id'] = ','.join(item_ids)

                logger.debug("Handling limit......")
                quota.handle_limit(max_quota=max_quota)

                response = requests.get(url, params=params)
                logger.debug(f"Getting request {response.url}.")
                response.raise_for_status()

                logging.info(
                    f"""
                    Getting data from Youtube Video API... 
                    {quota.units}/{max_quota} used...
                    """)

                quota.add_quota(unit_costs=api_cost_unit,
                                created_utc=datetime.now(tz=tz.UTC))

                logger.info(f"Inserting data to {endpoint}_api_response")

                with db:
                    try:
                        for i, item in enumerate(response.json()['items']):
                            item_id = item['id']
                            logger.info(
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
                logger.warning("NO MORE ITEMS TO RETRIEVE.")
                logger.info(f"""
                    RAW RESPONSES ARE IN {dbpath},
                    SCHEMA: {endpoint}_api_response.
                    """)
                break





