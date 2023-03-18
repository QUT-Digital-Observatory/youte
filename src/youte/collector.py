from __future__ import annotations

import json
import logging
import random
from datetime import datetime, timedelta
from typing import Iterator, Literal, Optional

import requests
from dateutil import tz

from youte._typing import APIResponse, SearchOrder
from youte.exceptions import APIError, InvalidRequest
from youte.utilities import create_utc_datetime_string

logger = logging.getLogger(__name__)


class Youte:
    def __init__(self, api_key: str):
        """Requires an API key to instantiate."""
        self.api_key: str = api_key

    def search(
        self,
        query: str,
        type_: str | list[str] = "video",
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        order: SearchOrder = "relevance",
        safe_search: Literal["moderate", "none", "strict"] = "none",
        language: Optional[str] = None,
        region: Optional[str] = None,
        video_duration: Literal["any", "long", "medium", "short"] = "any",
        channel_type: Literal["any", "show"] = "any",
        video_type: Literal["any", "episode", "movie"] = "any",
        caption: Literal["any", "closedCaption", "none"] = "any",
        video_definition: Literal["any", "high", "standard"] = "any",
        video_embeddable: Literal["any", "true"] = "any",
        video_license: Literal["any", "creativeCommon", "youtube"] = "any",
        video_dimension: Literal["2d", "3d", "any"] = "any",
        location: Optional[tuple] = None,
        location_radius: Optional[str] = None,
        max_result: int = 50,
        max_pages_retrieved: Optional[int] = None,
    ) -> Iterator[APIResponse]:
        """Do a YouTube search.

        Args:
            query (str): The term to search for.
                You can also use the Boolean NOT (-) and OR (|)
                operators to exclude videos or to find videos matching one of several
                search terms.
            type_ (str | list[str]): Type of resources to retrieve.
                Can be one or a list containing one or more
                of "channel", "video", "playlist"
            start_time (str, optional): Retrieve resources after this date.
                Has to be in YYYY-MM-DD format
            end_time (str, optional): Retrieve resources before this date.
                Has to be in YYYY-MM-DD format
            order ("date", "rating", "relevance", "title", "videoCount", "viewCount"):
                Sort results.
                - "date" sorts results in reverse chronological order.
                - "rating" sorts results from highest to lowest ratings.
                - "relevance" sorts results based on their relevance to the search query.
                - "title" sorts results alphabetically by title.
                - "videoCount" sorts channels in descending order of their number of videos.
                - "viewCount" sorts videos in descending order of views. For live broadcasts,
                videos are sorted by number of concurrent viewers while broadcasts are live.
            safe_search ("moderate", "none", "strict"): Include restricted content
                or not.
            language (str, optional): Return results most relevant to a language.
                Accepted values are ISO 639-1 two-letter language code.
            region (str, optional): Returns results that can be viewed in the specified
                country. Use ISO 3166-1 alpha-2 country code.
            video_duration ("any", "long", "medium", "short"): Filter results by video
                duration. type_ has to be "video".
            channel_type ("any", "show"): Filter results by channel type.
            video_type ("any", "episode", "movie"): Filter results by video type.
            caption ("any", "closedCaption", "none"): Filter results based on whether
                they have captions.
            video_definition ("any", "high", "standard"): Filter results by HD or SD
                videos.
            video_embeddable ("any", "true"): Restrict to only videos that can be
                embedded into a webpage.
            video_license ("any", "creativeCommon", "youtube"): Only include videos
                with a particular license.
            video_dimension ("2d", "3d", "any"): Only retrieve 2D or 3D videos.
            location (tuple, optional): Along with location_radius, defines a circular
                geographic area and restricts a search to videos that specify, in their
                metadata, a geographic location within that area. Both location and
                location_radius have to be specified.
                Input is a tuple of latitude/longitude coordinates, e.g.
                (37.42307,-122.08427).
            location_radius (str, optional): Along with location, defines a circular
                geographic area and restricts a search to videos that specify,
                in their metadata, a geographic location within that area.
                The parameter value must be a floating point number followed by a
                measurement unit. Valid measurement units are m, km, ft, and mi. Values
                larger than 1000 km are not supported.
            max_result (int): Maximum number of items that should be returned in one
                page of the result.
                Accepted values are between 0 and 50, inclusive.
            max_pages_retrieved (int, optional): Limit the number of result pages
                returned. Equals the maximum number of calls made to the API.

        Yields:
            Dict mappings containing API response.
        """

        url: str = r"https://www.googleapis.com/youtube/v3/search"
        params: dict = {
            "part": "snippet",
            "maxResults": max_result,
            "q": query,
            "type": type_ if isinstance(type_, str) else ",".join(type_),
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
            url=url, max_pages_retrieved=max_pages_retrieved, **params
        )

    def get_video_metadata(
        self,
        ids: list[str],
        part: Optional[list[str]] = None,
        max_results: int = 50,
    ) -> Iterator[APIResponse]:
        """Retrieve full metadata for videos using their IDs.

        Args:
            ids (list[str]): A list of one or multiple video IDs.
                If a single ID is specified, it should
                be wrapped in a list as well, e.g. ["video_id"].
            part (list[str], optional): A list of video resource properties that
                the API response will include. If not, these are the parts used:
                ["snippet", "statistics", "topicDetails",
                "status", "contentDetails", "recordingDetails", "id"].
            max_results (int):
                Maximum number of results returned in one page of response.
                Accepted value is between 0 and 50.

        Yields:
            Dict mappings containing API response.

        Raises:
            TypeError: If the value passed to ids is not a list, a TypeError will be raised.
        """
        url: str = r"https://www.googleapis.com/youtube/v3/videos"
        if part is None:
            part = [
                "snippet",
                "statistics",
                "topicDetails",
                "status",
                "contentDetails",
                "recordingDetails",
                "id",
                "liveStreamingDetails",
            ]
        params: dict = {
            "part": ",".join(part),
            "maxResults": max_results,
            "key": self.api_key,
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
            yield from _paginate_search_results(url=url, **params)

    def get_channel_metadata(
        self,
        ids: list[str],
        part: Optional[list[str]] = None,
        max_results: int = 50,
    ) -> Iterator[APIResponse]:
        """Retrieve full metadata for channels using their IDs.
        Currently, do not work with usernames. Channel IDs can be obtained in API
        responses to other methods such as search() or get_video_metadata().

        Args:
            ids (list[str]): A list of one or multiple channel IDs. If a single ID is
                specified, it should be wrapped in a list as well, e.g. ["video_id"].
            part (list[str], optional): A list of video resource properties that the
                API response will include.
                If nothing is passed, the parts used are [ "snippet", "statistics",
                "topicDetails", "status", "contentDetails", "brandingSettings",
                "contentOwnerDetails"]
            max_results (int):
                Maximum number of results returned in one page of response.
                Accepted value is between 0 and 50.

        Yields:
            Dict mappings containing API response.

        Raises:
            TypeError: If the value passed to ids is not a list,
                a TypeError will be raised.
        """
        url: str = r"https://www.googleapis.com/youtube/v3/channels"
        if part is None:
            part = [
                "snippet",
                "statistics",
                "topicDetails",
                "status",
                "contentDetails",
                "brandingSettings",
                "contentOwnerDetails",
            ]
        params: dict = {
            "part": ",".join(part),
            "maxResults": max_results,
            "key": self.api_key,
        }

        if ids and not isinstance(ids, list):
            raise TypeError("ids and username must be a list")

        while ids:
            ids = list(set(ids))
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
            yield from _paginate_search_results(url=url, **params)

    def get_comment_threads(
        self,
        video_ids: Optional[list[str]] = None,
        related_channel_ids: Optional[list[str]] = None,
        comment_ids: Optional[list[str]] = None,
        order: Literal["time", "relevance"] = "time",
        search_terms: Optional[str] = None,
        text_format: Literal["html", "plainText"] = "html",
        max_results: int = 100,
    ) -> Iterator[APIResponse]:
        """Retrieve comment threads (top-level comments) by their IDs, by video IDs, or
        by channel IDs.
        If video_ids are specified, retrieve all comment threads for
        those videos. If related_channel_ids are specified, retrieve all comments
        associated with those channels, including comments about the channels' videos.
        If comment_ids are specified, retrieve metadata of those comments.
        Exactly ONE of these parameters should be specified in one method call.

        Args:
            video_ids (list[str], optional):
                list of video IDs. If a single ID, wrap in list, too, e.g. ["video_id"].
                If this parameter is specified, the call will retrieve all comment threads
                on the specified videos. Nothing should be passed for related_channel_ids or
                comment_ids if this parameter is specified. A warning will be displayed if
                a video has disabled comments.
            related_channel_ids (list[str], optional):
                list of channel IDs. If a single ID, wrap in list, too, e.g. ["channel_id"].
                If this parameter is specified, retrieve all comment threads associated with
                these channels, including comments about the channels or the channels'
                videos. Nothing should be passed for video_ids or comment_ids if this
                parameter is specified.
            comment_ids (list[str], optional):
                list of comment IDs. If a single ID, wrap in list, too, e.g. ["cmt_id"].
                If this parameter is specified, retrieve metadata for all specified comment
                IDs. Nothing should be passed for video_ids or comment_ids if this
                parameter is specified.
            order ("time", "relevance"):
                How comment threads are sorted.
            search_terms (str, optional):
                Only retrieve comment threads matching search terms.
            text_format ("html", "plainText"):
                Specify the format of returned data.
            max_results (int):
                Maximum number of results returned in one page of response.
                Accepted value is between 0 and 100. Only applicable when retrieving
                comment threads using video or channel IDs. When comment IDs are provided,
                this argument is not used.

        Yields:
            Dict mappings containing API response.

        Raises:
            ValueError: If more than one of these parameters - video_ids,
                related_channel_ids, comment_ids - are specified, a ValueError
                will be raised.
        """

        if sum([bool(video_ids), bool(related_channel_ids), bool(comment_ids)]) > 1:
            raise ValueError(
                "Use only one of the following parameters: "
                "video_ids, related_channel_ids, comment_ids"
            )

        url: str = r"https://www.googleapis.com/youtube/v3/commentThreads"
        params: dict[str, str | int] = {
            "part": "snippet",
            "textFormat": text_format,
            "key": self.api_key,
        }

        if video_ids:
            params["order"] = order
            params["maxResults"] = max_results
            if search_terms:
                params["searchTerms"] = search_terms
            for video_id in video_ids:
                params["videoId"] = video_id
                yield from _paginate_search_results(url=url, **params)

        if related_channel_ids:
            params["order"] = order
            params["maxResults"] = max_results
            if search_terms:
                params["searchTerms"] = search_terms
            for channel_id in related_channel_ids:
                params["allThreadsRelatedToChannelId"] = channel_id
                yield from _paginate_search_results(url=url, **params)

        if comment_ids:
            url: str = r"https://www.googleapis.com/youtube/v3/commentThreads"

            comment_ids = list(set(comment_ids))
            while comment_ids:
                if len(comment_ids) <= 50:
                    ids_string = ",".join(comment_ids)
                    comment_ids = []
                else:
                    total_batches = int(len(comment_ids) / 50)
                    logger.info(f"{total_batches} pages remaining")
                    batch = random.sample(comment_ids, k=50)
                    ids_string = ",".join(batch)
                    for elm in batch:
                        comment_ids.remove(elm)

                params["id"] = ids_string
                yield from _paginate_search_results(url=url, **params)

    def get_thread_replies(
        self,
        thread_ids: list[str],
        text_format: Literal["html", "plainText"] = "html",
        max_results: int = 100,
    ) -> Iterator[APIResponse]:
        """Retrieve replies to comment threads. Currently, the API only supports getting
        replies to top-level comments. Replies to replies are not supported as of this
        version.

        Args:
            thread_ids (list[str]):
                list of comment thread IDs. If a single ID, wrap in list, too, e.g.
                ["thread_id"].
            text_format ("html", "plainText"):
                Specify the format of returned data.
            max_results (int):
                Maximum number of results returned in one page of response.
                Accepted value is between 0 and 100.

        Yields:
            Dict mappings containing API response.

        Raises:
            TypeError: If thread_ids is not a list, a TypeError will be raised.
        """
        url: str = r"https://www.googleapis.com/youtube/v3/comments"
        params: dict = {
            "part": "snippet",
            "maxResults": max_results,
            "textFormat": text_format,
            "key": self.api_key,
        }

        if thread_ids and not isinstance(thread_ids, list):
            raise TypeError("thread_ids must be a list")

        thread_ids = list(set(thread_ids))
        for thread_id in thread_ids:
            params["parentId"] = thread_id
            yield from _paginate_search_results(url=url, **params)

    def get_most_popular(
        self,
        region_code: str = "us",
        video_category_id: Optional[str] = None,
        max_results: int = 100,
        part: list[str] = None,
    ) -> Iterator[APIResponse]:
        """Retrieve the most popular videos for a region and video category.

        Args:
            region_code (str):
                ISO 3166-1 alpha-2 country code for specifying a region.
            video_category_id (str, optional):
                The video category ID for which the most popular videos should
                be retrieved.
            max_results (int):
                Maximum number of results to be retrieved per page.
            part (list[str], optional):
                A list of video resource properties that the API response will include.
                If noting is passed, the parts used are [ "snippet", "statistics",
                "topicDetails", "status", "contentDetails", "recordingDetails", "id"]

        Yields:
            Dict mappings containing API response.
        """
        url: str = r"https://www.googleapis.com/youtube/v3/videos"
        if part is None:
            part = [
                "snippet",
                "statistics",
                "topicDetails",
                "status",
                "contentDetails",
                "recordingDetails",
                "id",
            ]
        params: dict = {
            "part": part,
            "maxResults": max_results,
            "key": self.api_key,
            "chart": "mostPopular",
            "regionCode": region_code,
            "videoCategoryId": video_category_id,
        }

        yield from _paginate_search_results(url=url, **params)

    def get_related_videos(
        self,
        video_ids: list[str],
        region: Optional[str] = None,
        relevance_language: Optional[str] = None,
        safe_search: Literal["none", "moderate", "strict"] = "none",
        max_results: int = 50,
        max_pages_retrieved: Optional[int] = None,
    ) -> Iterator[APIResponse]:
        """Retrieve videos related to a specified video.
        Can iterate over a list of video IDs and retrieve related videos for each of the
        specified ID.

        Args:
            video_ids (list[str]):
                A list of video IDs for each of which to retrieve related videos. The
                function will iterate through each ID and get all related videos for that
                ID before moving on to the next. If a single ID is passed, wrap that in a
                list, too.
            region (str, optional):
                An ISO 3166-1 alpha-2 country code to specify the region that videos can be
                viewed in.
            relevance_language (str, optional):
                An ISO 639-1 two-letter language code to filter results most relevant to a
                language. Results in other languages will still be included if they are
                highly relevant to the video.
            safe_search ("none", "moderate", "strict"):
                Include restricted content or not.
            max_results (int):
                Maximum number of items that should be returned in one page of the result.
                Accepted values are between 0 and 50, inclusive.
            max_pages_retrieved (int, optional):
                Limit the number of result pages returned PER video ID.
                Equals the maximum number of calls made to the API PER video ID.
                So, if this parameter is set to 2 and a list of 3 IDs is specified
                for video_ids, that makes 6 calls to the API in total.

        Yields:
            Dict mappings containing API response.
        """
        url: str = r"https://www.googleapis.com/youtube/v3/search"
        params: dict = {
            "part": "snippet",
            "maxResults": max_results,
            "regionCode": region,
            "relevanceLanguage": relevance_language,
            "safeSearch": safe_search,
            "key": self.api_key,
            "type": "video",
        }

        for video_id in video_ids:
            params["relatedToVideoId"] = video_id
            for result in _paginate_search_results(
                url=url, max_pages_retrieved=max_pages_retrieved, **params
            ):
                result["related_to_video_id"] = video_id  # type: ignore
                yield result


def _paginate_search_results(
    url: str, max_pages_retrieved: Optional[int] = None, **kwargs
) -> Iterator[APIResponse]:
    page: int = 0
    logger.info(f"Getting page {page + 1}")
    r = _request(url=url, params=kwargs)
    page += 1
    response = _add_meta(r.json(), collection_time=datetime.now())
    yield response

    while "nextPageToken" in r.json():
        if max_pages_retrieved and page >= max_pages_retrieved:
            logger.info("Max pages reached")
            break
        else:
            logger.info(f"Getting page {page + 1}")
            next_page_token = r.json()["nextPageToken"]
            kwargs["pageToken"] = next_page_token
            r = _request(url=url, params=kwargs)
            page += 1
            response = _add_meta(r.json(), collection_time=datetime.now())
            yield response


def _add_meta(response: APIResponse, **kwargs) -> APIResponse:
    for key in kwargs:
        response[key] = kwargs[key]

    return response


def _request(url: str, params: dict[str, str | int]) -> requests.Response:
    response = requests.get(url, params=params)
    logger.debug(f"Getting {response.url}")
    logger.info(f"Status code: {response.status_code}")

    if response.status_code in [403, 400, 404]:
        try:
            errors = response.json()
        except requests.exceptions.JSONDecodeError:
            raise InvalidRequest("Check url and endpoint.")

        logger.error(f"Error {response.status_code}: {response.url}")
        logger.error(json.dumps(errors))

        for error in errors["error"]["errors"]:
            # ignore if comment is disabled
            if error["reason"] == "commentsDisabled":
                logger.warning(error["reason"])
            elif "quotaExceeded" in error["reason"]:
                until_reset = _get_reset_remaining(datetime.now(tz=tz.UTC))
                raise APIError(
                    f"{error['reason']}\n{until_reset} seconds til quota reset time"
                )
            else:
                raise APIError(error["message"])

    return response


def _get_reset_remaining(current: datetime) -> int:
    next_reset = datetime.now(tz=tz.gettz("US/Pacific")) + timedelta(days=1)
    next_reset = next_reset.replace(hour=0, minute=0, second=0, microsecond=0)
    reset_remaining = next_reset - current

    return reset_remaining.seconds + 1
