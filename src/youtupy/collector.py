import logging
import sqlite3
import requests
from requests import Response
from datetime import datetime
from dateutil import tz
import random
import json
import time
from typing import Union, List, Tuple
from pathlib import Path
import click
from tqdm import tqdm
from configobj import ConfigObj
import os
from math import ceil
import sys

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


def _load_page_token_from_file(filename: str) -> Tuple[List, str]:
    tokens = []

    # create a temporary 'history' config file
    if not os.path.exists(filename):
        history = ConfigObj(filename)
        tokens.append('')
    else:
        history = ConfigObj(filename)
        for key, value in history.items():
            if value == 'none':
                tokens.append(key)

    return tokens, history


def _request_with_error_handling(url, params):
    response = requests.get(url, params=params)
    logger.info(f'Getting {response.url}.\n'
                f'Status: {response.status_code}.')

    if response.status_code == 403:
        logger.error(f"Error: {response.url}")
        logger.error(
            response.json()['error']['message'])
        click.secho(response.json()['error']['message'],
                    fg='red',
                    bold=True)
        sys.exit()

    return response


def _write_output_to_jsonl(output_path, json_rec):
    logger.info(f'Writing output to {output_path}.')
    with open(output_path, 'a') as file:
        json_record = json.dumps(json_rec)
        file.write(json_record + '\n')


def _get_params(**kwargs):
    """Populate request parameters"""
    params = {}

    for key, value in kwargs.items():
        # proper datetime string formatting
        if (key == 'publishedAfter' or
                key == 'publishedBefore'):
            value = create_utc_datetime_string(value)
        params[key] = value

    return params


def _prompt_save_progress(filename):
    if os.path.exists(filename):
        if click.confirm('Do you want to save your '
                         'current progress?'):
            full_path = Path(filename).resolve()
            click.echo(f'Progress saved at {full_path}.')
        else:
            os.remove(filename)
    sys.exit()


def _get_page_token(response: Response,
                    saved_to: ConfigObj):
    try:
        next_page_token = response.json()['nextPageToken']
        saved_to[next_page_token] = 'none'
        saved_to.write()
    except KeyError:
        click.echo("No more page...")


class Youtupy:
    def __init__(self,
                 api_key: str,
                 max_quota: int = 10000):
        self.api_key = api_key
        self._quota = None
        self.max_quota = max_quota

    @property
    def quota(self):
        return self._quota

    @quota.setter
    def quota(self, quota: Quota):
        if isinstance(quota, Quota):
            self._quota = quota
        else:
            raise TypeError("Has to be a Quota object.")

    def search(self,
               query,
               output_path,
               **kwargs):
        api_cost = 100

        self.quota.get_quota()

        page = 1
        while True:
            try:
                tokens, history = _load_page_token_from_file('history')

                if not tokens:
                    break

                for token in tokens:

                    self.quota.handle_limit(max_quota=self.max_quota)

                    url = 'https://www.googleapis.com/youtube/v3/search'
                    params = _get_params(key=self.api_key,
                                         q=query,
                                         **kwargs)

                    if token != '':
                        params['pageToken'] = token

                    click.echo(f"Getting page {page} ⏳")

                    r = _request_with_error_handling(url=url,
                                                     params=params)

                    self.quota.add_quota(api_cost,
                                         datetime.now(tz=tz.UTC))

                    logger.info(f'Quota used: {self.quota.units}.')

                    _get_page_token(response=r, saved_to=history)

                    _write_output_to_jsonl(output_path=output_path,
                                           json_rec=r.json())

                    # store recorded and unrecorded tokens in config file
                    history['id'] = r.url
                    history[token] = datetime.now(tz=tz.UTC)
                    history.write()

                    page += 1

            except KeyboardInterrupt:
                click.echo()
                _prompt_save_progress(filename='history')

        click.secho(f'Complete! Total units used: {self.quota}',
                    fg='bright green')
        os.remove('history')

    def list_items(self,
                   item_type,
                   ids: List,
                   output_path,
                   by_parent_id=False,
                   by_channel_id=False,
                   by_video_id=False,
                   **kwargs):
        request_info = _get_endpoint(source)
        url = request_info['url']
        api_cost_unit = request_info['api_cost_unit']
        params = request_info['params']
        params['key'] = self.api_key

        for key, value in kwargs.items():
            params[key] = value

        # remove duplicate ids
        ids = list(set(ids))

        self.quota.get_quota()

        can_batch_ids = (item_type in ['channels', 'videos'] or
                         (item_type == 'comments' and not by_parent_id) or
                         (item_type == 'comment_threads' and not (
                                 by_video_id or
                                 by_channel_id)))

        cannot_batch_ids = ((item_type == 'comments' and by_parent_id) or
                            (item_type == 'comment_thread' and
                             (by_channel_id or by_video_id)))

        if can_batch_ids:

            while ids:
                batch_no = 1
                if len(ids) <= 50:
                    click.secho(f"Getting data ⏳")
                    ids_string = '.'.join(ids)
                    for elm in ids:
                        ids.remove(elm)
                else:
                    total_batches = int(ceil(len(ids) / 50))
                    click.echo(f"Getting batch {batch_no}/{total_batches} ⏳")
                    batch = random.sample(ids, k=50)
                    ids_string = '.'.join(batch)
                    for elm in batch:
                        ids.remove(elm)

                params['id'] = ids_string

                self.quota.handle_limit(max_quota=self.max_quota)

                r = _request_with_error_handling(url=url, params=params)

                self.quota.add_quota(api_cost_unit, datetime.now(tz=tz.UTC))
                logger.info(f'Quota used: {self.quota.units}.')

                _write_output_to_jsonl(output_path=output_path,
                                       json_rec=r.json())

                batch += 1

        elif cannot_batch_ids:

            for each in tqdm(ids):
                if by_parent_id:
                    params['parentId'] = each
                elif by_video_id:
                    params['videoId'] = each
                elif by_channel_id:
                    params['channelId'] = each

                while True:
                    tokens, history = _load_page_token_from_file('history')

                    if not tokens:
                        break

                    for token in tokens:
                        self.quota.handle_limit(max_quota=self.max_quota)
                        if token != '':
                            params['pageToken'] = token

                        _request_with_error_handling(url=url,
                                                     params=params)

                        self.quota.add_quota(api_cost_unit,
                                             datetime.now(tz=tz.UTC))
                        logger.info(f'Quota used: {self.quota.units}.')

                        _get_page_token(response=r,
                                        saved_to=history)

                        _write_output_to_jsonl(output_path=output_path,
                                               json_rec=r.json())

                        # store recorded and unrecorded tokens in config file
                        history[token] = datetime.now(tz=tz.UTC)
                        history.write()

                os.remove('history')
                click.secho('Completed!', fg='green')


class Collector:
    def __init__(self, api_key: str, max_quota: int = 10000):
        self.api_key = api_key
        self.params = None
        self.url = None
        self.output_path = None
        self.max_quota = max_quota
        self.quota = None

    def add_param(self, **param: Union[str, float]) -> None:
        for key, value in param.items():
            if (key == 'publishedAfter' or
                    key == 'publishedBefore'):
                value = create_utc_datetime_string(value)
            self.params[key] = value

    def add_quota(self, quota: Quota):
        self.quota = quota

    def get_data_by_ids(self,
                        source,
                        ids: List,
                        output_path,
                        by_parent_id=False,
                        by_channel_id=False,
                        by_video_id=False,
                        **kwargs):
        request_info = _get_endpoint(source)
        url = request_info['url']
        api_cost_unit = request_info['api_cost_unit']
        params = request_info['params']
        params['key'] = self.api_key

        for key, value in kwargs.items():
            params[key] = value

        # remove duplicate ids
        ids = list(set(ids))

        self.quota.get_quota()

        if (source in ['channels', 'videos'] or
                (source == 'comments' and not by_parent_id) or
                (source == 'comment_threads' and not (by_video_id or
                                                      by_channel_id))):

            while ids:
                batch_no = 1
                if len(ids) <= 50:
                    click.secho(f"Getting data ⏳")
                    ids_string = '.'.join(ids)
                    for elm in ids:
                        ids.remove(elm)
                else:
                    total_batches = int(ceil(len(ids) / 50))
                    click.echo(f"Getting batch {batch_no}/{total_batches} ⏳")
                    batch = random.sample(ids, k=50)
                    ids_string = '.'.join(batch)
                    for elm in batch:
                        ids.remove(elm)

                params['id'] = ids_string

                self.quota.handle_limit(max_quota=self.max_quota)

                r = requests.get(url, params=params)
                logger.info(f'Getting {r.url}.\n'
                            f'Status: {r.status_code}.')

                self.quota.add_quota(api_cost_unit, datetime.now(tz=tz.UTC))
                logger.info(f'Quota used: {self.quota.units}.')

                logger.info(f'Writing output to {output_path}.')
                with open(output_path, 'a+') as file:
                    json_record = json.dumps(r.json())
                    file.write(json_record + '\n')

                batch += 1

        elif ((source == 'comments' and by_parent_id) or
              (source == 'comment_thread' and (by_channel_id or
                                               by_video_id))):
            for each in tqdm(ids):
                if by_parent_id:
                    params['parentId'] = each
                elif by_video_id:
                    params['videoId'] = each
                elif by_channel_id:
                    params['channelId'] = each

                while True:
                    tokens = []
                    if not os.path.exists('history'):
                        history = ConfigObj('history')
                        tokens.append('')
                    else:
                        history = ConfigObj('history')
                        for key, value in history.items():
                            if value == 'none':
                                tokens.append(key)

                    if not tokens:
                        break

                    for token in tokens:
                        self.quota.handle_limit(max_quota=self.max_quota)
                        if token != '':
                            params['nextPageToken'] = token

                        r = requests.get(url, params=params)
                        logger.info(f'Getting {r.url}.\n'
                                    f'Status: {r.status_code}.')

                        r.raise_for_status()

                        self.quota.add_quota(api_cost_unit,
                                             datetime.now(tz=tz.UTC))
                        logger.info(f'Quota used: {self.quota.units}.')

                        try:
                            next_page_token = r.json()['nextPageToken']
                            history[next_page_token] = 'none'
                        except KeyError:
                            click.echo("No more page...")

                        # store recorded and unrecorded tokens in config file
                        history[token] = datetime.now(tz=tz.UTC)
                        history.write()

                        logger.info(f'Writing output to {output_path}.')
                        with open(output_path, 'a+') as file:
                            json_record = json.dumps(r.json())
                            file.write(json_record + '\n')

                os.remove('history')
                click.secho('Completed!', fg='green')


class SearchCollector:

    def __init__(self, api_key: str, max_quota: int = 10000):
        self.params = {
            'part': 'snippet',
            'maxResults': 50,
            'q': None,
            'type': 'video',
            'order': 'date',
            'safeSearch': 'none',
        }
        self.api_cost = 100
        self.url = 'https://www.googleapis.com/youtube/v3/search'
        self.output_path = None
        self.api_key = api_key
        self.max_quota = max_quota
        self.quota = None

    def add_param(self, **param: Union[str, float]) -> None:
        for key, value in param.items():
            if (key == 'publishedAfter' or
                    key == 'publishedBefore'):
                value = create_utc_datetime_string(value)
            self.params[key] = value

    def add_quota(self, quota: Quota):
        self.quota = quota

    def run(self, dbpath: str, warning=True) -> None:
        # validate and set up database
        dbpath = validate_file(dbpath, suffix='.db')

        if not dbpath.exists():
            logger.info(f"Creating {dbpath} at {dbpath.resolve().parent}.")
            click.echo()
            click.secho(f"Creating database file "
                        f"{dbpath} at {dbpath.resolve().parent}.",
                        fg='magenta')
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

        if warning:
            if ('publishedAfter' not in self.params and
                    'publishedBefore' not in self.params):
                click.secho("WARNING:",
                            fg='red',
                            bold=True)
                click.echo("No start date or end date is specified "
                           "for this request. "
                           "This might result in a large amount of "
                           "data being requested "
                           "and use up your available quota. ")
                click.confirm("Do you want to continue?", abort=True)

        self.params['key'] = self.api_key

        self.quota.get_quota()

        click.echo()
        click.echo("What you're looking for sounds interesting 👀! "
                   "Getting search results... ⏳")
        click.echo()

        logger.info(
            f"""
            Starting querying Youtube search results. 
            Quota unit cost will be {self.api_cost}.
            """)

        page = 1

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
                logger.debug("Getting new page tokens from database.")

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
                logger.info("No more items to retrieve.")
                break

            logger.debug("Handling limit...")
            self.quota.handle_limit(max_quota=self.max_quota)

            for token in to_retrieve:
                # if base url has not been requested yet, request base url

                if token == "":
                    r = requests.get(self.url, params=self.params)
                else:
                    self.params['pageToken'] = token
                    r = requests.get(self.url, params=self.params)

                self.quota.add_quota(unit_costs=self.api_cost,
                                     created_utc=datetime.now(tz=tz.UTC))

                logger.info(f"Retrieving data...\n"
                            f"{self.quota.units}/"
                            f"{self.max_quota} quota units used.\n"
                            f"Status: {r.status_code}")

                click.echo(f'Collecting page {page}.')
                # click.echo(f'Status: {r.status_code}')
                click.echo()

                logger.debug(
                    f"""
                    {r.url}
                    {r.status_code}
                    """)

                r.raise_for_status()

                if r.status_code == 403:
                    click.secho(r.json()['error']['message'],
                                fg='red',
                                bold=True)
                    continue

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
                    click.echo("End of search results reached.")
                    logger.info(f"End of results page reached.")
                    click.echo()

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

                time.sleep(1)
                page += 1

        process_to_database(source='search', dbpath=dbpath)
        total_results = [row[0] for
                         row in
                         sqlite3.connect(dbpath).execute(
                             """
                             SELECT COUNT(*)
                             FROM search_results
                             """
                         )][0]

        logger.info(
            f"SEARCH DATA COLLECTION COMPLETED.\n"
            f"{total_results} video results found "
            f"for keyword '{self.params['q']}'.\n"
            f"DATA IS STORED IN {dbpath} in location "
            f"{dbpath.resolve().parent}.\n"
            f" - RAW JSON IS STORED IN search_api_response SCHEMA.\n"
            f" - CLEAN DATA IS STORED IN search_results SCHEMA.\n"
        )

        click.secho(f"{total_results} videos found for "
                    f"keyword `{self.params['q']}`.\n"
                    f"Data is stored in {dbpath.resolve()}.",
                    fg="bright_green",
                    bold=True)
        click.echo(f'Total quota units used: {self.quota.units}.')

    def get_enriching_data(self, endpoint: ['video', 'channel']):
        click.echo()
        endpoint_url = _get_endpoint(endpoint)['url']
        endpoint_api_cost = _get_endpoint(endpoint)['api_cost_unit']
        endpoint_params = _get_endpoint(endpoint)['params']
        endpoint_params['key'] = self.api_key

        if not self.output_path:
            raise InvalidRequestParameter("No search results found. "
                                          "Do a Youtube search request first.")
        else:
            db = sqlite3.connect(self.output_path)

            insert_ids_to_db(self.output_path,
                             source=endpoint,
                             table=f"{endpoint}_api_response")

            self.quota.get_quota()

            total_results = [row[0] for
                             row in
                             db.execute(
                                 f"""
                                 SELECT COUNT(*)
                                 FROM {endpoint}_api_response
                                 """
                             )][0]

            batches = int(int(total_results) / 50)

            click.secho(f"Getting detailed {endpoint} data ⏳...",
                        fg='magenta')

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
                    self.quota.handle_limit(max_quota=self.max_quota)

                    r = requests.get(endpoint_url,
                                     params=endpoint_params)
                    logger.debug(f"Getting request {r.url}.")
                    r.raise_for_status()

                    logger.info(f"Retrieving additional {endpoint} data...\n"
                                f"{self.quota.units}/"
                                f"{self.max_quota} quota units used.\n"
                                f"Status: {r.status_code}")

                    logger.debug(
                        f"""
                        {r.url}
                        {r.status_code}
                        """)

                    self.quota.add_quota(unit_costs=endpoint_api_cost,
                                         created_utc=datetime.now(
                                             tz=tz.UTC))

                    logger.debug(
                        f"Inserting data to {endpoint}_api_response")

                    with db:
                        for item in r.json()['items']:
                            try:
                                item_id = item['id']
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
                                click.secho(
                                    f"WARNING: data on some {endpoint}s "
                                    f"could not be found.\n"
                                    f"See log for more details.",
                                    fg='yellow')
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

                    time.sleep(1)

                else:
                    logger.info(f"No more {endpoint} items to retrieve.")
                    logger.info(f"RAW RESPONSES ARE IN {self.output_path}\n"
                                f"SCHEMA: {endpoint}_api_response.")
                    break

            process_to_database(source=endpoint, dbpath=self.output_path)
            logger.info(
                f"{endpoint.upper()} DATA COLLECTION COMPLETED. "
                f"DATA IS STORED IN {self.output_path} in location "
                f"{Path(self.output_path).resolve().parent}.\n"
                f" - RAW JSON IS STORED IN {endpoint}_api_response SCHEMA."
                f"\n"
                f" - CLEAN DATA IS STORED IN {endpoint}_results SCHEMA."
            )
            click.secho(f"All {endpoint} data have been collected!",
                        fg='bright_green')
            click.echo(f'Total quota units used: {self.quota.units}.')

    def get_comments(self, replies=False, **kwargs):
        """Get comments of videos found in search results"""

        # get comment threads
        cmtthread_url = _get_endpoint('comment_thread')['url']
        cmtthread_api_cost = _get_endpoint('comment_thread')['api_cost_unit']

        if not self.output_path:
            raise InvalidRequestParameter("No search results found. "
                                          "Do a Youtube search request first.")
        else:
            db = sqlite3.connect(self.output_path)

            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS comment_checks(
                    video_id PRIMARY KEY,
                    retrieval_time
                    );

                CREATE TABLE IF NOT EXISTS comment_threads_api_response(
                     next_page_token,
                     video_id,
                     request_url,
                     status_code,
                     response,
                     retrieval_time,
                     PRIMARY KEY (next_page_token, video_id)
                     );
                """
            )
            db.commit()

            insert_ids_to_db(self.output_path,
                             source='video',
                             table='comment_checks')

            self.quota.get_quota()

            click.echo()
            click.secho(f"Getting comment data ⏳...",
                        fg='magenta')

            while True:

                item_ids = [row[0]
                            for row in
                            db.execute(
                                """
                               SELECT video_id
                               FROM comment_checks
                               WHERE retrieval_time IS NULL
                               """)]

                if not item_ids:
                    logger.info("Comment thread collection finished.")
                    break

                else:
                    for item_id in tqdm(item_ids):
                        cmtthread_params = _get_endpoint('comment_thread')[
                            'params']
                        cmtthread_params['key'] = self.api_key
                        cmtthread_params['videoId'] = item_id

                        logger.debug("Handling limit......")
                        self.quota.handle_limit(max_quota=self.max_quota)

                        while True:

                            with db:
                                # empty string for the base request url
                                # because it doesn't have a page token

                                db.execute(
                                    """
                                    INSERT OR IGNORE INTO
                                      comment_threads_api_response(
                                        next_page_token,
                                        video_id
                                        )
                                    VALUES (?,?)
                                    """,
                                    ('', item_id)
                                )

                                # get list of unrecorded page tokens
                                logger.debug("Getting new page tokens "
                                             "from database.")

                                to_retrieve = set(
                                    row[0]
                                    for row in db.execute(
                                        f"""
                                        SELECT next_page_token
                                        FROM comment_threads_api_response
                                        WHERE retrieval_time IS NULL
                                          AND video_id = ?
                                        """,
                                        (item_id,))
                                )

                            if not len(to_retrieve):
                                logger.info("No more items to retrieve.")
                                break
                            else:
                                logger.debug("Handling limit...")
                                self.quota.handle_limit(
                                    max_quota=self.max_quota)

                                for token in to_retrieve:
                                    # if base url has not been requested yet,
                                    # request base url

                                    if token == "":
                                        r = requests.get(cmtthread_url,
                                                         params=cmtthread_params)
                                    else:
                                        cmtthread_params[
                                            'pageToken'] = token
                                        r = requests.get(cmtthread_url,
                                                         params=cmtthread_params)

                                    self.quota.add_quota(unit_costs=
                                                         cmtthread_api_cost,
                                                         created_utc=
                                                         datetime.now(
                                                             tz=tz.UTC))

                                    logger.info(f"Getting comment "
                                                f"threads for "
                                                f"video {item_id}, "
                                                f"token {token}.\n"
                                                f"Status: {r.status_code}.\n"
                                                f"Total quota used: "
                                                f"{self.quota.units}")

                                    if r.status_code == 403:
                                        logger.error(f"Error: {item_id}")
                                        logger.error(
                                            r.json()['error']['message'])

                                        errors_message = r.json()['error'][
                                            'errors']

                                        for error in errors_message:
                                            logger.error(
                                                f"Item {item_id}: "
                                                f"{error['reason']}")

                                            # ignore if comment is disabled
                                            # for the video
                                            if (error['reason'] ==
                                                    'commentsDisabled'):
                                                click.secho('WARNING',
                                                            fg='bright_red',
                                                            bold=True)
                                                click.secho(
                                                    f"{r.json()['error']['message']}",
                                                    fg="bright_red",
                                                    bold=True
                                                )
                                                db.execute(
                                                    """
                                                    REPLACE INTO
                                                    comment_threads_api_response(
                                                        next_page_token,
                                                        video_id,
                                                        retrieval_time
                                                        )
                                                    VALUES (?,?,?)
                                                    """,
                                                    (token,
                                                     item_id,
                                                     datetime.now(
                                                         tz=tz.UTC))
                                                )
                                            else:
                                                click.secho('ERROR',
                                                            fg='red',
                                                            bold=True)
                                                click.secho(
                                                    f"{r.json()['error']['message']}",
                                                    fg="red",
                                                    bold=True
                                                )
                                                r.raise_for_status()
                                        continue

                                    # get nextPageToken from current response
                                    # and insert it to the database

                                    try:
                                        next_page_token = r.json()[
                                            'nextPageToken']

                                        db.execute(
                                            """
                                            INSERT OR IGNORE INTO
                                            comment_threads_api_response(
                                                next_page_token, video_id)
                                            VALUES (?,?)
                                            """,
                                            (next_page_token, item_id))

                                    except KeyError as e:
                                        logger.info(
                                            f"End of results page reached.")

                                    # update database with response
                                    # from current request
                                    db.execute(
                                        """
                                        REPLACE INTO
                                        comment_threads_api_response(
                                            next_page_token,
                                            video_id,
                                            request_url,
                                            status_code,
                                            response,
                                            retrieval_time
                                            )
                                        VALUES (?,?,?,?,?,?)
                                        """,
                                        (token,
                                         item_id,
                                         r.url,
                                         r.status_code,
                                         json.dumps(r.json()),
                                         datetime.utcnow())
                                    )

                                    time.sleep(1)

                                logger.debug("Inserting database...")
                                db.execute(
                                    """
                                    REPLACE INTO comment_checks(
                                        video_id,
                                        retrieval_time
                                        )
                                    VALUES (?,?)
                                    """,
                                    (item_id, datetime.now(tz=tz.UTC))
                                )

        process_to_database(source='comment_thread',
                            dbpath=self.output_path)

        click.secho(f"All comment data have been collected!",
                    fg='bright_green')
        click.echo(f'Total quota units used: {self.quota.units}.')

        # get replies to comments
        if replies:
            comment_url = _get_endpoint('comment')['url']
            comment_api_cost = _get_endpoint('comment')[
                'api_cost_unit']

            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS reply_api_response(
                         next_page_token,
                         comment_id,
                         request_url,
                         status_code,
                         response,
                         retrieval_time,
                         PRIMARY KEY (next_page_token, comment_id)
                         );
                         
                INSERT OR IGNORE INTO reply_api_response(next_page_token,
                                                         comment_id)
                    SELECT '', thread_id
                    FROM comment_threads
                    WHERE reply_count > 0;
                """
            )
            db.commit()

            click.echo()
            click.secho(f"Getting comment reply data ⏳...",
                        fg='magenta')

            while True:
                comment_ids = [row[0]
                               for row in
                               db.execute(
                                   """
                                   SELECT comment_id
                                   FROM reply_api_response
                                   WHERE retrieval_time IS NULL
                                   """
                               )]

                if not comment_ids:
                    logger.info("No items to retrieve. Collection completed.")
                    break
                else:
                    for comment_id in tqdm(comment_ids):
                        logger.info(
                            f"Getting replies for comment {comment_id}.")

                        logger.debug("Handling limit...")
                        self.quota.handle_limit(max_quota=self.max_quota)

                        while True:
                            to_retrieve = set(
                                row[0]
                                for row in db.execute(
                                    f"""
                                     SELECT next_page_token 
                                     FROM reply_api_response
                                     WHERE retrieval_time IS NULL
                                       AND comment_id = ?
                                    """,
                                    (comment_id,))
                            )

                            if not len(to_retrieve):
                                logger.info("No more items to retrieve.")
                                break
                            else:
                                logger.debug("Handling limit...")
                                self.quota.handle_limit(
                                    max_quota=self.max_quota)

                                for token in to_retrieve:
                                    comment_params = \
                                        _get_endpoint('comment')['params']
                                    comment_params['key'] = self.api_key
                                    comment_params['parentId'] = comment_id

                                    if token != "":
                                        comment_params['pageToken'] = token

                                    r = requests.get(comment_url,
                                                     params=comment_params)

                                    self.quota.add_quota(unit_costs=
                                                         comment_api_cost,
                                                         created_utc=
                                                         datetime.now(
                                                             tz=tz.UTC))

                                    logger.info(f"Getting replies for"
                                                f" comment {comment_id}, "
                                                f"token {token}.\n"
                                                f"Status: {r.status_code}.\n"
                                                f"Total quota used: "
                                                f"{self.quota.units}.")

                                    if r.status_code == 403:
                                        logger.error(
                                            f"Error: {comment_id}")
                                        logger.error(
                                            r.json()['error']['message'])
                                        errors_message = r.json()['error'][
                                            'errors']
                                        for error in errors_message:
                                            logger.error(
                                                f"Reason: {error['reason']}")
                                            if (error['reason'] ==
                                                    'commentsDisabled'):
                                                db.execute(
                                                    """
                                                    REPLACE INTO 
                                                    reply_api_response(
                                                        next_page_token,
                                                        comment_id,
                                                        retrieval_time
                                                        )
                                                    VALUES (?,?,?)
                                                    """,
                                                    (token,
                                                     comment_id,
                                                     datetime.now(
                                                         tz=tz.UTC))
                                                )
                                            else:
                                                click.secho('ERROR',
                                                            fg='red',
                                                            bold=True)
                                                click.secho(
                                                    f"{r.json()['error']['message']}",
                                                    fg="red",
                                                    bold=True
                                                )
                                                r.raise_for_status()
                                        continue

                                    db.execute("BEGIN TRANSACTION")
                                    try:
                                        next_page_token = r.json()[
                                            'nextPageToken']

                                        db.execute(
                                            """
                                            INSERT OR IGNORE INTO 
                                            reply_api_response(next_page_token,
                                                               comment_id) 
                                            VALUES (?,?)
                                            """,
                                            (next_page_token, comment_id))

                                    except KeyError as e:
                                        logger.info(
                                            f"End of results page reached.")

                                    # update database with response
                                    # from current request
                                    db.execute(
                                        """
                                        REPLACE INTO 
                                        reply_api_response(
                                            next_page_token,
                                            comment_id,
                                            request_url,
                                            status_code,
                                            response,
                                            retrieval_time
                                            )
                                        VALUES (?,?,?,?,?,?)
                                        """,
                                        (token,
                                         comment_id,
                                         r.url,
                                         r.status_code,
                                         json.dumps(r.json()),
                                         datetime.now(tz=tz.UTC))
                                    )
                                    db.execute("COMMIT")
                                    time.sleep(1)

            process_to_database(source='reply',
                                dbpath=self.output_path)
            click.secho("All comment reply data collected!",
                        fg='bright_green',
                        bold=True)
            click.echo(f'Total quota units used: {self.quota.units}.')


def _get_endpoint(endpoint) -> dict:
    """Get all the request details needed to make an API request to
    specified endpoints.

    Position argument: endpoint -- either 'search', 'video', 'channel',
    'commentThread', or 'comment'
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
                'key': None
            }
        },

        'comment_thread': {
            'url': r'https://www.googleapis.com/youtube/v3/commentThreads',
            'api_cost_unit': 1,
            'params': {
                'part': 'snippet',
                'maxResults': 100,
                'order': 'time'
            }
        },

        'comment': {
            'url': r'https://www.googleapis.com/youtube/v3/comments',
            'api_cost_unit': 1,
            'params': {
                'part': 'snippet',
                'maxResults': 100
            }
        }
    }

    return api_endpoints[endpoint]
