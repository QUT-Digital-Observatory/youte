from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Literal, Optional

from youte.common import Resources


@dataclass
class Search:
    kind: str
    id: str
    published_at: datetime
    title: str
    description: str
    thumbnail_url: str
    thumbnail_width: int
    thumbnail_height: int
    channel_title: str
    live_broadcast_content: str


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
    tags: List[str]
    category_id: str
    localized_title: str
    localized_description: str
    default_language: str
    default_audio_language: str
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
    like_count: int
    comment_count: int
    topic_categories: Optional[List[str]]
    live_streaming_start_actual: Optional[datetime]
    live_streaming_end_actual: Optional[datetime]
    live_streaming_start_scheduled: Optional[datetime]
    live_streaming_end_scheduled: Optional[datetime]
    live_streaming_concurrent_viewers: Optional[int]


@dataclass
class Videos(Resources):
    items: List[Video]


@dataclass
class Channel:
    kind: str
    id: str
    title: str
    description: str
    custom_url: str
    published_at: datetime
    thumbnail_url: str
    thumbnail_height: int
    thumbnail_width: int
    default_language: str
    localized_title: str
    localized_description: str
    country: str
    view_count: int
    subscriber_count: int
    hidden_subscriber_count: bool
    video_count: int
    topic_categories: List[str]
    privacy_status: Literal["private", "public", "unlisted"]
    is_linked: bool
    made_for_kids: bool
    branding_keywords: List[str]
    moderated_comments: bool


@dataclass
class Channels(Resources):
    items: List[Channel]


@dataclass
class Comment:
    id: str
    channel_id: str
    video_id: str
    parent_id: str
    can_reply: bool
    total_reply_count: int
    is_public: bool
    author_display_name: str
    author_profile_image_url: str
    author_channel_url: str
    author_channel_id: str
    text_display: str
    text_original: str
    can_rate: bool
    viewer_rating: Literal["like", "none"]
    like_count: str
    published_at: datetime
    updated_at: datetime


@dataclass
class Comments(Resources):
    items: List[Comment]
