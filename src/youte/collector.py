import json
import logging
import os
import random
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import (
    Mapping, 
    Literal, 
    Union, 
    Optional, 
    TypedDict, 
    Generator, 
    List, 
    Tuple,
    Dict
)

import click
import requests
from dateutil import tz
from tqdm import tqdm

from youte.exceptions import StopCollector
from youte.utilities import create_utc_datetime_string
from youte._typing import SearchOrder

logger = logging.getLogger(__name__)


class SearchResult(TypedDict):
    kind: str
    etag: str
    id: dict
    nextPageToken: str
    prevPageToken: str
    regionCode: str
    pageInfo: dict
    items: List[dict]


def _request_with_error_handling(
        url: str,
        params: Mapping[str, Union[str, int]]
        ) -> requests.Response:
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

def _prompt_save_progress(filename) -> None:
    if os.path.exists(filename):
        if click.confirm("Do you want to save your current progress?"):
            full_path = Path(filename).resolve()
            click.echo(f"Progress saved at {full_path}")
        else:
            os.remove(filename)
    sys.exit()


# def _get_page_token(response: requests.Response, saved_to: ProgressSaver) -> None:
#     try:
#         next_page_token = response.json()["nextPageToken"]
#         saved_to.add_token(next_page_token)
#     except KeyError:
#         logger.info("No more page...")


def _get_reset_remaining(current: datetime) -> int:
    next_reset = datetime.now(tz=tz.gettz("US/Pacific")) + timedelta(days=1)
    next_reset = next_reset.replace(hour=0, minute=0, second=0, microsecond=0)
    reset_remaining = next_reset - current

    return reset_remaining.seconds + 1


class Youte:
    def __init__(self, api_key: str):
        self.api_key: str = api_key

    def search(
        self,
        query: str,
        type_: str = "video",
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        order: SearchOrder = "relevance",
        safe_search: Literal["moderate", "none", "strict"] = "none",
        language: Optional[str] = None,
        region: Optional[str] = None,
        video_duration: Literal["any", "high", "standard"] = "any",
        channel_type: Literal["any", "show"] = "any",
        video_type: Literal["any", "episode", "movie"] = "any",
        caption: Literal["any", "closedCaption", "none"] = "any",
        video_definition: Literal["any", "high", "standard"] = "any",
        video_embeddable: Literal["any", "true"] = "any",
        video_license: Literal["any", "creativeCommon", "youtube"] = "any",
        video_dimension: Literal["2d", "3d", "any"] = "any",
        location: Optional[Tuple] = None,
        location_radius: Optional[str] = None,
        max_result: int = 50,
        max_pages_retrieved: Optional[int] = None
    ) -> Generator[SearchResult, None, None]:

        url: str = r"https://www.googleapis.com/youtube/v3/search"
        params: dict = {
            "part": "snippet",
            "maxResults": max_result,
            "q": query,
            "type": type_,
            "order": order,
            "safeSearch": safe_search,
            "key": self.api_key,
            "publishedAfter": create_utc_datetime_string(start_time),
            "publishedBefore": create_utc_datetime_string(end_time),
            "videoDuration": video_duration,
            "channelType": channel_type,
            "location": str(location) if location else location,
            "locationRadius": location_radius,
            "videoCaption": caption,
            "videoDefinition": video_definition,
            "videoDimension": video_dimension,
            "videoEmbeddable": video_embeddable,
            "videoLicense": video_license,
            "videoType": video_type,
            "relevanceLanguage": language,
            "regionCode": region,
        }

        yield from _paginate_search_results(
            url=url,
            max_pages_retrieved=max_pages_retrieved,
            **params
        )
        
    def get_video_metadata(
        self,
        ids: List[str],
        part: Optional[str] = "snippet,statistics,topicDetails,status,contentDetails,recordingDetails,id",
        max_results: Optional[int] = 50
    ) -> Generator[Dict, None, None]:
        
        url: str = r"https://www.googleapis.com/youtube/v3/videos"
        params: dict = {
            "part": part,
            "maxResults": max_results,
            "key": self.api_key
        }

        if not isinstance(ids, list):
            raise TypeError("ids must be a list")

        ids = list(set(ids))

        while ids:
            if len(ids) <= 50:
                ids_string = ",".join(ids)
                ids = []
            else:
                total_batches = int(len(ids) / 50)
                logger.info(f"{total_batches} pages remaining")
                batch = random.sample(ids, k=50)
                ids_string = ",".join(batch)
                for elm in batch:
                    ids.remove(elm)

            params["id"] = ids_string
            yield from _paginate_search_results(
                url=url,
                **params
            )

    def get_channel_metadata(
        self,
        ids: Optional[List[str]] = None,
        part: Optional[str] = "snippet,statistics,topicDetails,status,contentDetails,brandingSettings,contentOwnerDetails",
        max_results: int = 50
    ) -> Generator[Dict, None, None]:
        url: str = r"https://www.googleapis.com/youtube/v3/channels"
        params: dict = {
            "part": part,
            "maxResults": max_results,
            "key": self.api_key
        }

        if not isinstance(ids, list):
            raise TypeError("ids and username must be a list")

        ids = list(set(ids))

        while ids:
            if len(ids) <= 50:
                ids_string = ",".join(ids)
                ids = []
            else:
                total_batches = int(len(ids) / 50)
                logger.info(f"{total_batches} pages remaining")
                batch = random.sample(ids, k=50)
                ids_string = ",".join(batch)
                for elm in batch:
                    ids.remove(elm)

            params["id"] = ids_string
            yield from _paginate_search_results(
                url=url,
                **params
            )
        
        # Get by username not working atm, not sure why

        # while username:
        #     if len(username) <= 50:
        #         username_string = ",".join(username)
        #         ids = []
        #     else:
        #         total_batches = int(len(username) / 50)
        #         logger.info(f"{total_batches} pages remaining")
        #         batch = random.sample(username, k=50)
        #         username_string = ",".join(batch)
        #         for elm in batch:
        #             username.remove(elm)

        #     params["forUsername"] = username_string
        #     yield from _paginate_search_results(
        #         url=url,
        #         **params
        #     )

    def get_comment_threads(
        self,
        video_ids: Optional[List[str]] = None,
        related_channel_ids: Optional[List[str]] = None,
        comment_ids: Optional[List[str]] = None,
        order: Literal["time", "relevance"] = "time",
        search_terms: Optional[str] = None,
        text_format: Optional[str] = "html",
        max_results: int = 100
    ):
        if sum(
            [bool(video_ids), bool(related_channel_ids), bool(comment_ids is True)]
            ) > 1:
            raise ValueError(
                "Use only one of the following paramaters: "
                "video_ids, related_channel_ids, comment_ids")
        
        url: str = r"https://www.googleapis.com/youtube/v3/commentThreads"
        params: Dict = {
            "part": "snippet",
            "maxResults": max_results,
            "textFormat": text_format,
            "key": self.api_key
        }

        if video_ids:
            params["order"] = order
            if search_terms:
                params["searchTerms"] = search_terms
            for video_id in video_ids:
                params["videoId"] = video_id
                yield from _paginate_search_results(
                    url=url,
                    **params
                )
        
        if related_channel_ids:
            params["order"] = order
            if search_terms:
                params["searchTerms"] = search_terms
            for channel_id in related_channel_ids:
                params["allThreadsRelatedToChannelId"] = channel_id
                yield from _paginate_search_results(
                    url=url,
                    **params
                )

        if comment_ids:
            url: str = r"https://www.googleapis.com/youtube/v3/comment"

            comment_ids = list(set(comment_ids))
            while comment_ids:
                if len(comment_ids) <= 50:
                    ids_string = ",".join(comment_ids)
                    ids = []
                else:
                    total_batches = int(len(comment_ids) / 50)
                    logger.info(f"{total_batches} pages remaining")
                    batch = random.sample(comment_ids, k=50)
                    ids_string = ",".join(batch)
                    for elm in batch:
                        comment_ids.remove(elm)

                params["id"] = ids_string
                yield from _paginate_search_results(
                    url=url,
                    **params
                )        

    def get_thread_replies(
        self,
        thread_ids: List[str],
        text_format: Optional[str] = "html",
        max_results: int = 100
    ):
        url: str = r"https://www.googleapis.com/youtube/v3/comment"
        params: Dict = {
            "part": "snippet",
            "maxResults": max_results,
            "textFormat": text_format,
            "key": self.api_key
        }

        thread_ids = list(set(thread_ids))
        for thread_id in thread_ids:
            params["parentId"] = thread_id
            yield from _paginate_search_results(
                url=url,
                **params
            )

    # def list_most_popular(
    #     self,
    #     region_code: str = None,
    #     video_category: str = None,
    # ) -> Mapping:
    #     request_info = _get_endpoint("videos")
    #     url = request_info["url"]
    #     params = request_info["params"]
    #     params["key"] = self.api_key
    #     params["chart"] = "mostPopular"

    #     if region_code:
    #         params["regionCode"] = region_code
    #     elif video_category:
    #         params["videoCategoryId"] = video_category

    #     history_file = _get_history_path(f"history_{time.time()}.db")

    #     try:
    #         while True:
    #             if "pageToken" in params:
    #                 del params["pageToken"]

    #             tokens, history = _load_page_token(history_file)

    #             if not tokens:
    #                 logger.info("No more token found.")
    #                 break

    #             for token in tokens:
    #                 if token != "":
    #                     logger.info("Adding page token...")
    #                     params["pageToken"] = token

    #                 r = _request_with_error_handling(url=url, params=params)

    #                 _get_page_token(response=r, saved_to=history)

    #                 # store recorded and unrecorded tokens
    #                 history.update_token(token)

    #                 yield r.json()

    #     except KeyboardInterrupt:
    #         sys.exit(1)

    #     finally:
    #         history.close()
    #         if history_file.exists():
    #             os.remove(history_file)


def _paginate_search_results(
        url,
        max_pages_retrieved: Optional[int] = None,
        **kwargs) ->  Generator[Dict, None, None]:
    page: int = 0
    logger.info("getting requests")
    r = _request_with_error_handling(url=url, params=kwargs)
    page += 1
    yield r.json()
    

    while "nextPageToken" in r.json():
        if max_pages_retrieved and page >= max_pages_retrieved:
            break
        else:
            next_page_token = r.json()["nextPageToken"]
            kwargs["pageToken"] = next_page_token
            r = _request_with_error_handling(url=url, params=kwargs)
            page += 1
            yield r.json()







