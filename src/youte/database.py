from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

import sqlalchemy.exc
from sqlalchemy.engine import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from youte.resources import Channels, Comments, Searches, Videos

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


class Search(Base):
    __tablename__ = "search"

    id: Mapped[str] = mapped_column(primary_key=True)
    kind: Mapped[str]
    published_at: Mapped[str]
    title: Mapped[str]
    description: Mapped[str]
    channel_id: Mapped[str]
    thumbnail_width: Mapped[int]
    thumbnail_height: Mapped[int]
    channel_title: Mapped[str]
    live_broadcast_content: Mapped[str]


class Video(Base):
    __tablename__ = "video"

    id: Mapped[str] = mapped_column(primary_key=True)
    kind: Mapped[str]
    published_at: Mapped[str]
    channel_id: Mapped[str]
    title: Mapped[str]
    description: Mapped[str]
    thumbnail_url: Mapped[str]
    thumbnail_width: Mapped[int]
    thumbnail_height: Mapped[int]
    channel_title: Mapped[str]
    tags: Mapped[Optional[str]]
    category_id: Mapped[str]
    localized_title: Mapped[str]
    localized_description: Mapped[str]
    default_language: Mapped[Optional[str]]
    default_audio_language: Mapped[Optional[str]]
    duration: Mapped[str]
    dimension: Mapped[str]
    definition: Mapped[str]
    caption: Mapped[bool]
    licensed_content: Mapped[bool]
    projection: Mapped[str]
    upload_status: Mapped[str]
    privacy_status: Mapped[str]
    license: Mapped[str]
    embeddable: Mapped[bool]
    public_stats_viewable: Mapped[bool]
    made_for_kids: Mapped[bool]
    view_count: Mapped[int]
    like_count: Mapped[Optional[int]]
    comment_count: Mapped[Optional[int]]
    topic_categories: Mapped[Optional[str]]
    live_streaming_start_actual: Mapped[Optional[str]]
    live_streaming_end_actual: Mapped[Optional[str]]
    live_streaming_start_scheduled: Mapped[Optional[str]]
    live_streaming_end_scheduled: Mapped[Optional[str]]
    live_streaming_concurrent_viewers: Mapped[Optional[int]]


class Channel(Base):
    __tablename__ = "channel"

    kind: Mapped[str]
    id: Mapped[str] = mapped_column(primary_key=True)
    title: Mapped[str]
    description: Mapped[str]
    custom_url: Mapped[Optional[str]]
    published_at: Mapped[datetime]
    thumbnail_url: Mapped[str]
    thumbnail_height: Mapped[int]
    thumbnail_width: Mapped[int]
    default_language: Mapped[Optional[str]]
    localized_title: Mapped[str]
    localized_description: Mapped[str]
    country: Mapped[Optional[str]]
    view_count: Mapped[Optional[int]]
    subscriber_count: Mapped[Optional[int]]
    hidden_subscriber_count: Mapped[bool]
    video_count: Mapped[int]
    topic_categories: Mapped[Optional[str]]
    privacy_status: Mapped[str]
    is_linked: Mapped[bool]
    made_for_kids: Mapped[Optional[bool]]
    branding_keywords: Mapped[Optional[str]]
    moderated_comments: Mapped[Optional[bool]]


class Comment(Base):
    __tablename__ = "comment"

    id: Mapped[str] = mapped_column(primary_key=True)
    video_id: Mapped[Optional[str]]
    parent_id: Mapped[Optional[str]]
    can_reply: Mapped[Optional[bool]]
    total_reply_count: Mapped[Optional[int]]
    is_public: Mapped[Optional[bool]]
    author_display_name: Mapped[str]
    author_profile_image_url: Mapped[str]
    author_channel_url: Mapped[str]
    author_channel_id: Mapped[str]
    text_display: Mapped[str]
    text_original: Mapped[str]
    can_rate: Mapped[bool]
    viewer_rating: Mapped[str]
    like_count: Mapped[int]
    published_at: Mapped[str]
    updated_at: Mapped[str]


def set_up_database(db_path: str | Path, echo: bool = False) -> Engine:
    """Create all required tables in an SQLite database.

    Args:
        db_path: path of the SQlite database
        echo: if True, log all statements as well as a repr() of their parameter lists
            to the default log handler, which defaults to sys.stdout for output

    Returns:
        An Engine instance which can be used to update and query data from the database
    """
    engine = create_engine(f"sqlite:///{db_path}", echo=echo)
    tables = Base.metadata.tables.keys()
    logger.info("Creating database tables")
    logger.debug(f"Creating tables {tables}")
    Base.metadata.create_all(engine)
    logger.debug("Tables created.")
    return engine


def type_check(func) -> Callable:
    """Decorator to type check database populating functions"""

    def new_func(engine, data):
        if not isinstance(data, list):
            raise TypeError(f"data is type {type(data)}, not list")

        if not isinstance(engine, Engine):
            raise TypeError(f"engine must be Engine, not {type(engine)}")

        func(engine=engine, data=data)

    return new_func


@type_check
def populate_searches(engine: Engine, data: list[Searches]) -> None:
    """Populate search data into a database.

    Args:
        engine: an Engine instance that has been initiated using
            youte.database.set_up_database()
        data: a list of Searches object

    Returns
        No value is returned as the function interacts with the database only.
    """
    with Session(engine) as s:
        for page in data:
            for search in page.items:
                search_data = Search(
                    id=search.id,
                    title=search.title,
                    kind=search.kind,
                    published_at=search.published_at,
                    description=search.description,
                    thumbnail_width=search.thumbnail_width,
                    thumbnail_height=search.thumbnail_height,
                    channel_title=search.channel_title,
                    channel_id=search.channel_id,
                    live_broadcast_content=search.live_broadcast_content,
                )
                try:
                    s.add(search_data)
                    s.commit()
                except sqlalchemy.exc.IntegrityError as e:
                    logger.warning(f"{search_data.id} - {search_data.title}: {e}")
                    s.rollback()


@type_check
def populate_videos(engine: Engine, data: list[Videos]) -> None:
    """Populate video data into a database.

    Args:
        engine: an Engine instance that has been initiated using
            youte.database.set_up_database()
        data: a list of Videos object

    Returns
        No value is returned as the function interacts with the database only.
    """
    with Session(engine) as s:
        for page in data:
            for video in page.items:
                video_data = Video(
                    id=video.id,
                    title=video.title,
                    kind=video.kind,
                    published_at=video.published_at,
                    channel_id=video.channel_id,
                    description=video.description,
                    thumbnail_width=video.thumbnail_width,
                    thumbnail_height=video.thumbnail_height,
                    thumbnail_url=video.thumbnail_url,
                    channel_title=video.channel_title,
                    tags=str(video.tags),
                    category_id=video.category_id,
                    localized_title=video.localized_title,
                    localized_description=video.localized_description,
                    default_language=video.default_language,
                    default_audio_language=video.default_audio_language,
                    duration=video.duration,
                    dimension=video.dimension,
                    definition=video.definition,
                    caption=video.caption,
                    licensed_content=video.licensed_content,
                    projection=video.projection,
                    upload_status=video.upload_status,
                    privacy_status=video.privacy_status,
                    license=video.license,
                    embeddable=video.embeddable,
                    public_stats_viewable=video.public_stats_viewable,
                    made_for_kids=video.made_for_kids,
                    view_count=video.view_count,
                    like_count=video.like_count,
                    comment_count=video.comment_count,
                    topic_categories=str(video.topic_categories),
                    live_streaming_start_actual=video.live_streaming_start_actual,
                    live_streaming_end_actual=video.live_streaming_end_actual,
                    live_streaming_start_scheduled=video.live_streaming_start_scheduled,
                    live_streaming_end_scheduled=video.live_streaming_end_scheduled,
                    live_streaming_concurrent_viewers=video.live_streaming_concurrent_viewers,
                )
                try:
                    s.add(video_data)
                    s.commit()
                except sqlalchemy.exc.IntegrityError as e:
                    logger.warning(f"{video_data.id} - {video_data.title}: {e}")
                    s.rollback()


@type_check
def populate_channels(engine: Engine, data: list[Channels]) -> None:
    """Populate channel data into a database.

    Args:
        engine: an Engine instance that has been initiated using
            youte.database.set_up_database()
        data: a list of Channels object

    Returns
        No value is returned as the function interacts with the database only.
    """
    with Session(engine) as s:
        for page in data:
            for channel in page.items:
                channel_data = Channel(
                    id=channel.id,
                    kind=channel.kind,
                    title=channel.title,
                    description=channel.description,
                    custom_url=channel.custom_url,
                    published_at=channel.published_at,
                    thumbnail_url=channel.thumbnail_url,
                    thumbnail_height=channel.thumbnail_height,
                    thumbnail_width=channel.thumbnail_width,
                    default_language=channel.default_language,
                    localized_title=channel.localized_title,
                    localized_description=channel.localized_description,
                    country=channel.country,
                    view_count=channel.view_count,
                    subscriber_count=channel.subscriber_count,
                    hidden_subscriber_count=channel.hidden_subscriber_count,
                    video_count=channel.video_count,
                    topic_categories=str(channel.topic_categories),
                    privacy_status=channel.privacy_status,
                    is_linked=channel.is_linked,
                    made_for_kids=channel.made_for_kids,
                    branding_keywords=str(channel.branding_keywords),
                    moderated_comments=channel.moderated_comments,
                )
                try:
                    s.add(channel_data)
                    s.commit()
                except sqlalchemy.exc.IntegrityError as e:
                    logger.warning(f"{channel_data.id} - {channel_data.title}: {e}")
                    s.rollback()


@type_check
def populate_comments(engine: Engine, data: list[Comments]) -> None:
    """Populate channel data into a database.

    Args:
        engine: an Engine instance that has been initiated using
            youte.database.set_up_database()
        data: a list of Comments object

    Returns
        No value is returned as the function interacts with the database only.
    """
    with Session(engine) as s:
        for page in data:
            for cmt in page.items:
                cmt_data = Comment(
                    id=cmt.id,
                    video_id=cmt.video_id,
                    parent_id=cmt.parent_id,
                    can_reply=cmt.can_reply,
                    total_reply_count=cmt.total_reply_count,
                    is_public=cmt.is_public,
                    author_display_name=cmt.author_display_name,
                    author_profile_image_url=cmt.author_profile_image_url,
                    author_channel_url=cmt.author_channel_url,
                    author_channel_id=cmt.author_channel_id,
                    text_display=cmt.text_display,
                    text_original=cmt.text_original,
                    can_rate=cmt.can_rate,
                    viewer_rating=cmt.viewer_rating,
                    like_count=cmt.like_count,
                    published_at=cmt.published_at,
                    updated_at=cmt.updated_at,
                )
                try:
                    s.add(cmt_data)
                    s.commit()
                except sqlalchemy.exc.IntegrityError as e:
                    logger.warning(f"{cmt_data.id}: {e}")
                    s.rollback()
