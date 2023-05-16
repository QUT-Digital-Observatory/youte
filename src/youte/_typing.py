import datetime
import sys
from typing import List, Literal, TypedDict, Union

if sys.version_info < (3, 11):
    from typing_extensions import NotRequired
else:
    from typing import NotRequired


SearchOrder = Literal["date", "rating", "relevance", "title", "videoCount", "viewCount"]


class SearchResult(TypedDict):
    kind: str
    etag: str
    id: dict
    nextPageToken: str
    prevPageToken: str
    regionCode: str
    pageInfo: dict
    items: List[dict]
    related_to_video_id: NotRequired[str]
    _youte: NotRequired[dict]


class StandardResult(TypedDict):
    kind: str
    etag: str
    nextPageToken: str
    pageInfo: dict
    items: List[dict]
    _youte: NotRequired[dict]


class VideoChannelResult(TypedDict):
    kind: str
    etag: str
    id: dict
    nextPageToken: str
    prevPageToken: str
    pageInfo: dict
    items: List[dict]
    _youte: NotRequired[dict]


APIResponse = Union[SearchResult, StandardResult, VideoChannelResult]
