from __future__ import annotations

import sqlalchemy.exc
from sqlalchemy.engine import create_engine, Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session
from typing import Optional
import logging
from pathlib import Path

from youte.resources import Searches, Videos

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
    tags: Mapped[str]
    category_id: Mapped[str]
    localized_title: Mapped[str]
    localized_description: Mapped[str]
    default_language: Mapped[str]
    default_audio_language: Mapped[str]
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
    like_count: Mapped[int]
    comment_count: Mapped[int]
    topic_categories: Mapped[Optional[str]]
    live_streaming_start_actual: Mapped[Optional[str]]
    live_streaming_end_actual: Mapped[Optional[str]]
    live_streaming_start_scheduled: Mapped[Optional[str]]
    live_streaming_end_scheduled: Mapped[Optional[str]]
    live_streaming_concurrent_viewers: Mapped[Optional[int]]


def set_up_database(db_path: str | Path, echo: bool = True) -> Engine:
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


def populate_searches(engine: Engine, data: list[Searches]) -> None:
    """Populate search data into a database.

    Args:
        engine: an Engine instance that has been initiated using
            youte.database.set_up_database()
        data: a list of Searches object

    Returns
        No value is returned as the function interacts with the database only.
    """
    if not isinstance(data, list):
        raise TypeError(f"data is type {type(data)}, not list")

    if not isinstance(engine, Engine):
        raise TypeError(f"engine must be Engine, not {type(engine)}")

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
                        live_broadcast_content=search.live_broadcast_content,
                    )
                try:
                    s.add(search_data)
                    s.commit()
                except sqlalchemy.exc.IntegrityError as e:
                    logger.warning(f"{search_data.id} - {search_data.title}: {e}")
                    s.rollback()


def populate_videos(engine: Engine, data: list[Videos]) -> None:
    """Populate video data into a database.

    Args:
        engine: an Engine instance that has been initiated using
            youte.database.set_up_database()
        data: a list of Videos object

    Returns
        No value is returned as the function interacts with the database only.
    """
    if not isinstance(data, list):
        raise TypeError(f"data is type {type(data)}, not list")

    if not isinstance(engine, Engine):
        raise TypeError(f"engine must be Engine, not {type(engine)}")

    with Session(engine) as s:
        for page in data:
            for video in page.items:
                video_data = Video(
                        id=video.id,
                        title=video.title,
                        kind=video.kind,
                        published_at=video.published_at,
                        description=video.description,
                        thumbnail_width=video.thumbnail_width,
                        thumbnail_height=video.thumbnail_height,
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
                        live_streaming_concurrent_viewers=video.live_streaming_concurrent_viewers
                    )
                try:
                    s.add(video_data)
                    s.commit()
                except sqlalchemy.exc.IntegrityError as e:
                    logger.warning(f"{video_data.id} - {video_data.title}: {e}")
                    s.rollback()