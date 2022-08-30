import logging
import sqlite3
import requests
from datetime import datetime
from dateutil import tz
import random
import json
import time
from typing import List, Tuple, Mapping
from pathlib import Path
import click
from tqdm import tqdm
import os
import sys
from typing import Union

from youte.quota import Quota
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

    def close(self) -> None:
        self.conn.close()


def _confirm_existing_history(filename: str) -> None:
    if os.path.exists(filename):
        confirm_text = f"""
        A history file '{filename}' is detected in your current directory.
        Do you want to resume progress from this history file?
        If you are at all unsure, say No."""
        confirm_prompt = click.confirm(confirm_text)

        if not confirm_prompt:
            os.remove(filename)


def _load_page_token(filename) -> Tuple[List, ProgressSaver]:
    history = ProgressSaver(path=filename)
    tokens = history.load_token()

    return tokens, history


def _request_with_error_handling(url: str, params: Mapping) -> requests.Response:
    response = requests.get(url, params=params)
    logger.info(f"Getting {response.url}.\nStatus: {response.status_code}.")

    if response.status_code in [403, 400, 404]:
        logger.error(f"Error: {response.url}")
        logger.error(f"Error: {params}")

        errors = response.json()["error"]["errors"]
        for error in errors:
            # ignore if comment is disabled
            if error["reason"] == "commentsDisabled":
                click.secho("WARNING:", fg="bright_red", bold=True)
                click.secho(error["reason"], fg="bright_red", bold=True)
            else:
                click.secho("ERROR:", fg="red", bold=True)
                click.secho(
                    "An error has occurred in making the request.", fg="red", bold=True
                )
                click.secho(f"Reason: {error['message']}", fg="red", bold=True)
                logger.error(json.dumps(response.json()))
                sys.exit(1)

    time.sleep(1)

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
        if click.confirm("Do you want to save your " "current progress?"):
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
    history_dir = Path('.youte.history')

    if not history_dir.exists():
        os.mkdir(history_dir)

    db_file = Path(outfile).with_suffix('.db')

    return history_dir / db_file.name


class Youte:
    def __init__(self, api_key: str, max_quota: int = 10000):
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

    def search(self, query, output_path, **kwargs):
        api_cost = 100

        self.quota.get_quota()

        page = 0

        history_file = _get_history_path(output_path)
        _confirm_existing_history(history_file)

        while True:
            try:
                tokens, history = _load_page_token(history_file)

                if not tokens:
                    break

                for token in tokens:
                    page += 1

                    self.quota.handle_limit(max_quota=self.max_quota)

                    url = "https://www.googleapis.com/youtube/v3/search"

                    params = _get_params(key=self.api_key, q=query, **kwargs)

                    if token != "":
                        params["pageToken"] = token

                    click.echo(f"Getting page {page}")

                    r = _request_with_error_handling(url=url, params=params)

                    self.quota.add_quota(api_cost, datetime.now(tz=tz.UTC))

                    logger.info(f"Quota used: {self.quota.units}.")

                    _get_page_token(response=r, saved_to=history)

                    _write_output_to_jsonl(output_path=output_path, json_rec=r.json())

                    # store recorded and unrecorded tokens in config file
                    history.update_token(token)

            except KeyboardInterrupt:
                click.echo()
                history.close()
                _prompt_save_progress(filename=history_file)

        click.secho(
            f"Complete! {page} pages of search results collected.\n"
            f"Total units used: {self.quota.units}",
            fg="bright_green",
        )
        history.close()
        os.remove(history_file)

    def list_items(
        self,
        item_type,
        ids: List,
        output_path,
        by=None,
        saved_to="history.db",
        **kwargs,
    ):
        request_info = _get_endpoint(item_type)
        url = request_info["url"]
        api_cost_unit = request_info["api_cost_unit"]
        params = request_info["params"]
        params["key"] = self.api_key

        for key, value in kwargs.items():
            params[key] = value

        ids = list(set(ids))

        self.quota.get_quota()

        # SET COLLECTOR TYPE
        # YouTube endpoints fall into 2 categories:
        # 1. A comma-separated list of ids can be passed in the request param
        # 2. Only a single id can be passed in the request param

        valid_by_values = ["parent", "video"]

        if by and by not in valid_by_values:
            raise ValueError("`by` must be `parent` or `video`")

        is_channel_video = item_type in ["channels", "videos"]
        get_comments_only = (item_type == "comment_threads") and (
            not (by == "parent" or by == "video")
        )
        get_by_parents = (item_type == "comments") and by == "parent"
        get_by_video_channel = (item_type == "comment_threads") and (by == "video")

        can_batch_ids = is_channel_video or get_comments_only
        cannot_batch_ids = get_by_parents or get_by_video_channel

        if get_comments_only:
            del params["maxResults"]

        if can_batch_ids:
            logger.info("Batching ids")
            batch_no = 0
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

                self.quota.handle_limit(max_quota=self.max_quota)

                r = _request_with_error_handling(url=url, params=params)

                self.quota.add_quota(api_cost_unit, datetime.now(tz=tz.UTC))
                logger.info(f"Quota used: {self.quota.units}.")

                _write_output_to_jsonl(output_path=output_path, json_rec=r.json())

                batch_no += 1

            click.echo(
                f"{batch_no} pages collected.\n"
                f"Total quota used: {self.quota.units}."
            )

        elif cannot_batch_ids:

            history_file = _get_history_path(output_path)

            for each in tqdm(ids):

                if by == "parent":
                    params["parentId"] = each
                elif by == "video":
                    params["videoId"] = each

                while True:
                    try:
                        if "pageToken" in params:
                            del params["pageToken"]

                        tokens, history = _load_page_token(history_file)

                        if not tokens:
                            logger.info("No more token found.")
                            break

                        for token in tokens:
                            self.quota.handle_limit(max_quota=self.max_quota)

                            if token != "":
                                logger.info("Adding page token...")
                                params["pageToken"] = token

                            r = _request_with_error_handling(url=url, params=params)

                            self.quota.add_quota(api_cost_unit, datetime.now(tz=tz.UTC))
                            logger.info(f"Quota used: {self.quota.units}.")

                            _get_page_token(response=r, saved_to=history)

                            _write_output_to_jsonl(
                                output_path=output_path, json_rec=r.json()
                            )

                            # store recorded and unrecorded tokens
                            history.update_token(token)

                    except KeyboardInterrupt:
                        if history_file.exists():
                            history.close()
                            os.remove(history_file)
                        sys.exit(1)

                history.close()
                os.remove(history_file)

            click.secho("Completed!", fg="green")
            click.secho(f"File saved in {output_path}", fg="green")


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
                "part": "snippet,statistics,topicDetails,status,"
                "contentDetails,recordingDetails,id",
                "id": None,
                "maxResults": 50,
                "key": None,
            },
        },
        "channels": {
            "url": r"https://www.googleapis.com/youtube/v3/channels",
            "api_cost_unit": 1,
            "params": {
                "part": "snippet,statistics,topicDetails,status,"
                "contentDetails,brandingSettings,contentOwnerDetails",
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
