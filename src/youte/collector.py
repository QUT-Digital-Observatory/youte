import json
import logging
import os
import random
import sqlite3
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Mapping, Tuple, Union

import click
import requests
from dateutil import tz
from tqdm import tqdm

from youte.exceptions import StopCollector
from youte.utilities import create_utc_datetime_string

logger = logging.getLogger(__name__)


class ProgressSaver:
    def __init__(self, path):
        self.path = path
        self.conn = sqlite3.connect(path, isolation_level=None)

    def load_token(self) -> List:
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS history (
                next_page_token PRIMARY KEY,
                retrieval_time
                );

            CREATE TABLE IF NOT EXISTS meta (
                id INT CHECK (id=1) UNIQUE,
                params
                );

            INSERT OR IGNORE INTO history(next_page_token)
            VALUES ("");
            """
        )

        tokens = [
            row[0]
            for row in self.conn.execute(
                """
                SELECT next_page_token FROM history
                WHERE retrieval_time IS NULL
                """
            )
        ]

        return tokens

    def update_token(self, token: str) -> None:
        self.conn.execute(
            "REPLACE INTO history VALUES (?,?)", (token, datetime.now(tz=tz.UTC))
        )
        self.conn.commit()

    def add_token(self, token: str) -> None:
        self.conn.execute(
            """
            INSERT OR IGNORE INTO history(next_page_token)
            VALUES (?)
            """,
            (token,),
        )
        self.conn.commit()

    def add_meta(self, params: Mapping) -> None:
        self.conn.execute(
            """
            INSERT OR IGNORE INTO meta
            VALUES (?, ?)
            """,
            (1, json.dumps(params)),
        )

    def get_meta(self) -> Mapping:
        params = [row[0] for row in self.conn.execute("SELECT params FROM meta")]
        if len(params) > 1:
            logger.error("Something is seriously wrong!")
        else:
            return json.loads(params[0])

    def close(self) -> None:
        self.conn.close()


def _load_page_token(filename) -> Tuple[List, ProgressSaver]:
    history = ProgressSaver(path=filename)
    tokens = history.load_token()

    return tokens, history


def _request_with_error_handling(url: str, params: Mapping) -> requests.Response:
    response = requests.get(url, params=params)
    logger.info(f"Getting {response.url}.\nStatus: {response.status_code}.")

    if response.status_code in [403, 400, 404]:
        errors = response.json()["error"]["errors"]

        logger.error(f"Error: {response.url}")
        logger.error(json.dumps(errors))

        for error in errors:
            # ignore if comment is disabled
            if error["reason"] == "commentsDisabled":
                logger.warning(error["reason"])
            elif "quotaExceeded" in error["reason"]:
                # wait until reset time if quota exceeded
                until_reset = _get_reset_remaining(datetime.now(tz=tz.UTC))

                logger.error(error["reason"])
                click.echo(error["reason"])
                logger.warning(f"Sleeping for {until_reset} seconds til reset time")
                click.echo(f"Sleeping for {until_reset} seconds til reset time")
                time.sleep(until_reset)
                _request_with_error_handling(url, **params)
            else:
                logger.error(f"Reason: {error['message']}")
                logger.error(json.dumps(response.json()))
                click.echo(f"{error['message']}")
                sys.exit(1)

    return response


def _write_output_to_jsonl(output_path: str, json_rec: Mapping) -> None:
    logger.info(f"Writing output to {output_path}.")
    with open(output_path, "a") as file:
        json_record = json.dumps(json_rec)
        file.write(json_record + "\n")


def _get_params(**kwargs) -> dict:
    """Populate request parameters"""
    params = {}

    for key, value in kwargs.items():
        # proper datetime string formatting
        if key == "publishedAfter" or key == "publishedBefore":
            value = create_utc_datetime_string(value)
        params[key] = value

    return params


def _prompt_save_progress(filename) -> None:
    if os.path.exists(filename):
        if click.confirm("Do you want to save your current progress?"):
            full_path = Path(filename).resolve()
            click.echo(f"Progress saved at {full_path}")
        else:
            os.remove(filename)
    sys.exit()


def _get_page_token(response: requests.Response, saved_to: ProgressSaver) -> None:
    try:
        next_page_token = response.json()["nextPageToken"]
        saved_to.add_token(next_page_token)
    except KeyError:
        logger.info("No more page...")


def _get_history_path(outfile: Union[str, Path]) -> Path:
    history_dir = Path(".youte.history")

    if not history_dir.exists():
        os.mkdir(history_dir)

    db_file = Path(outfile).with_suffix(".db")

    return history_dir / db_file.name


def _get_reset_remaining(current: datetime) -> int:
    next_reset = datetime.now(tz=tz.gettz("US/Pacific")) + timedelta(days=1)
    next_reset = next_reset.replace(hour=0, minute=0, second=0, microsecond=0)
    reset_remaining = next_reset - current

    return reset_remaining.seconds + 1


class Youte:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.history_file = None

    def search(
        self, save_progress_to: Union[str, Path] = None, limit: int = None, **kwargs
    ) -> dict:
        page = 0

        if not save_progress_to:
            save_progress_to = f"search_{int(time.time())}.db"

        history_file = _get_history_path(save_progress_to)
        self.history_file = history_file

        try:
            while True:
                tokens, history = _load_page_token(history_file)

                history.add_meta(kwargs)

                if not tokens:
                    break

                for token in tokens:
                    page += 1

                    if limit and page > limit:
                        if history_file.exists():
                            os.remove(history_file)
                        sys.exit(0)

                    url = "https://www.googleapis.com/youtube/v3/search"

                    params = _get_params(key=self.api_key, **kwargs)

                    if token != "":
                        params["pageToken"] = token

                    click.echo(f"Getting page {page}")

                    r = _request_with_error_handling(url=url, params=params)

                    _get_page_token(response=r, saved_to=history)

                    # store recorded and unrecorded tokens in config file
                    history.update_token(token)

                    yield r.json()

            history.close()

            if history_file.exists():
                os.remove(history_file)

        except KeyboardInterrupt:
            raise StopCollector()

        finally:
            if history_file.exists():
                history.close()

    def list_items(
        self,
        item_type,
        ids: List,
        by=None,
        save_progress_to: Union[str, Path] = "history.db",
        **kwargs,
    ):
        valid_type = ["videos", "channels", "comments", "comment_threads"]

        if item_type not in valid_type:
            raise ValueError(f"`item_type` must be one of {valid_type}")

        request_info = _get_endpoint(item_type)
        url = request_info["url"]
        params = request_info["params"]
        params["key"] = self.api_key

        for key, value in kwargs.items():
            params[key] = value

        ids = list(set(ids))

        # SET COLLECTOR TYPE
        # YouTube endpoints fall into 2 categories:
        # 1. A comma-separated list of ids can be passed in the request param
        # 2. Only a single id can be passed in the request param

        valid_by_values = ["parent", "video"]

        if by and by not in valid_by_values:
            raise ValueError("`by` must be `parent` or `video`")

        not_comments = item_type in ["channels", "videos"]
        get_comments_only = (item_type == "comments") and (
            not (by == "parent" or by == "video")
        )
        get_by_parents = (item_type == "comments") and by == "parent"
        get_by_video_channel = (item_type == "comment_threads") and (by == "video")

        can_batch_ids = not_comments or get_comments_only
        cannot_batch_ids = get_by_parents or get_by_video_channel

        if get_comments_only:
            del params["maxResults"]

        if can_batch_ids:
            logger.info("Batching ids")
            click.secho("Getting data")
            while ids:
                if len(ids) <= 50:
                    ids_string = ",".join(ids)
                    ids = None
                else:
                    total_batches = int(len(ids) / 50)
                    click.echo(f"{total_batches} pages remaining")
                    batch = random.sample(ids, k=50)
                    ids_string = ",".join(batch)
                    for elm in batch:
                        ids.remove(elm)

                params["id"] = ids_string
                r = _request_with_error_handling(url=url, params=params)
                yield r.json()

        elif cannot_batch_ids:
            history_file = _get_history_path(save_progress_to)

            for each in tqdm(ids):
                if by == "parent":
                    params["parentId"] = each
                elif by == "video":
                    params["videoId"] = each

                try:
                    while True:
                        if "pageToken" in params:
                            del params["pageToken"]

                        tokens, history = _load_page_token(history_file)

                        if not tokens:
                            logger.info("No more token found.")
                            break

                        for token in tokens:
                            if token != "":
                                logger.info("Adding page token...")
                                params["pageToken"] = token

                            r = _request_with_error_handling(url=url, params=params)

                            _get_page_token(response=r, saved_to=history)

                            # store recorded and unrecorded tokens
                            history.update_token(token)

                            yield r.json()

                except KeyboardInterrupt:
                    sys.exit(1)

                finally:
                    history.close()
                    if history_file.exists():
                        os.remove(history_file)

    def list_most_popular(
        self,
        region_code: str = None,
        video_category: str = None,
    ) -> Mapping:
        request_info = _get_endpoint("videos")
        url = request_info["url"]
        params = request_info["params"]
        params["key"] = self.api_key
        params["chart"] = "mostPopular"

        if region_code:
            params["regionCode"] = region_code
        elif video_category:
            params["videoCategoryId"] = video_category

        history_file = _get_history_path(f"history_{time.time()}.db")

        try:
            while True:
                if "pageToken" in params:
                    del params["pageToken"]

                tokens, history = _load_page_token(history_file)

                if not tokens:
                    logger.info("No more token found.")
                    break

                for token in tokens:
                    if token != "":
                        logger.info("Adding page token...")
                        params["pageToken"] = token

                    r = _request_with_error_handling(url=url, params=params)

                    _get_page_token(response=r, saved_to=history)

                    # store recorded and unrecorded tokens
                    history.update_token(token)

                    yield r.json()

        except KeyboardInterrupt:
            sys.exit(1)

        finally:
            history.close()
            if history_file.exists():
                os.remove(history_file)


def _get_endpoint(endpoint) -> dict:
    """Get all the request details needed to make an API request to
    specified endpoints.

    Position argument: endpoint -- either 'search', 'video', 'channel',
    'commentThread', or 'comment'
    """
    api_endpoints = {
        "search": {
            "url": r"https://www.googleapis.com/youtube/v3/search",
            "api_cost_unit": 100,
            "params": {
                "part": "snippet",
                "maxResults": 50,
                "q": None,
                "type": "video",
                "order": "date",
                "safeSearch": "none",
                "key": None,
            },
        },
        "videos": {
            "url": r"https://www.googleapis.com/youtube/v3/videos",
            "api_cost_unit": 1,
            "params": {
                "part": (
                    "snippet,statistics,topicDetails,status,"
                    "contentDetails,recordingDetails,id"
                ),
                "id": None,
                "maxResults": 50,
                "key": None,
            },
        },
        "channels": {
            "url": r"https://www.googleapis.com/youtube/v3/channels",
            "api_cost_unit": 1,
            "params": {
                "part": (
                    "snippet,statistics,topicDetails,status,"
                    "contentDetails,brandingSettings,contentOwnerDetails"
                ),
                "id": None,
                "maxResults": 50,
                "key": None,
            },
        },
        "comment_threads": {
            "url": r"https://www.googleapis.com/youtube/v3/commentThreads",
            "api_cost_unit": 1,
            "params": {"part": "snippet", "maxResults": 100, "order": "time"},
        },
        "comments": {
            "url": r"https://www.googleapis.com/youtube/v3/comments",
            "api_cost_unit": 1,
            "params": {"part": "snippet", "maxResults": 100},
        },
    }

    return api_endpoints[endpoint]
