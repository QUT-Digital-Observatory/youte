from __future__ import annotations

from datetime import datetime
from typing import Any, List, Literal, Optional

from pydantic.dataclasses import dataclass

from youte.common import Resources


@dataclass
class Search:
    kind: str
    id: str
    published_at: datetime
    title: str
    description: str
    channel_id: str
    thumbnail_url: str
    thumbnail_width: int
    thumbnail_height: int
    channel_title: str
    live_broadcast_content: str
    meta: dict


@dataclass
class Searches(Resources):
    items: List[Search]


@dataclass
class Video:
    kind: str
    id: str
    published_at: datetime
    channel_id: str
    title: str
    description: str
    thumbnail_url: str
    thumbnail_width: int
    thumbnail_height: int
    channel_title: str
    tags: Optional[List[str]]
    category_id: str
    localized_title: str
    localized_description: str
    default_language: Optional[str]
    default_audio_language: Optional[str]
    duration: str
    dimension: str
    definition: Literal["hd", "sd"]
    caption: bool
    licensed_content: bool
    projection: Literal["360", "rectangular"]
    upload_status: str
    privacy_status: Literal["private", "public", "unlisted"]
    license: Literal["creativeCommon", "youtube"]
    embeddable: bool
    public_stats_viewable: bool
    made_for_kids: bool
    view_count: int
    like_count: Optional[int]
    comment_count: Optional[int]
    topic_categories: Optional[List[str]]
    live_streaming_start_actual: Optional[datetime]
    live_streaming_end_actual: Optional[datetime]
    live_streaming_start_scheduled: Optional[datetime]
    live_streaming_end_scheduled: Optional[datetime]
    live_streaming_concurrent_viewers: Optional[int]
    meta: dict


@dataclass
class Videos(Resources):
    items: List[Video]


@dataclass
class Channel:
    kind: str
    id: str
    title: str
    description: str
    custom_url: Optional[str]
    published_at: datetime
    thumbnail_url: str
    thumbnail_height: int
    thumbnail_width: int
    default_language: Optional[str]
    localized_title: str
    localized_description: str
    country: Optional[str]
    view_count: Optional[str]
    subscriber_count: Optional[str]
    hidden_subscriber_count: bool
    video_count: int
    topic_categories: Optional[List[str]]
    privacy_status: Literal["private", "public", "unlisted"]
    is_linked: bool
    made_for_kids: Optional[bool]
    branding_keywords: Optional[List[str]]
    moderated_comments: Optional[bool]
    meta: dict


@dataclass
class Channels(Resources):
    items: List[Channel]


@dataclass
class Comment:
    id: str
    video_id: Optional[str]
    parent_id: Optional[str]
    can_reply: Optional[bool]
    total_reply_count: Optional[int]
    is_public: Optional[bool]
    author_display_name: str
    author_profile_image_url: str
    author_channel_url: str
    author_channel_id: str
    text_display: str
    text_original: str
    can_rate: bool
    viewer_rating: Literal["like", "none"]
    like_count: int
    published_at: datetime
    updated_at: datetime
    meta: dict


@dataclass
class Comments(Resources):
    items: List[Comment]
