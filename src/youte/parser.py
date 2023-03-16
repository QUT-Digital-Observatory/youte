from __future__ import annotations

import html
from datetime import datetime
from typing import Iterable, Iterator, Optional

from youte._typing import SearchResult, StandardResult, VideoChannelResult
from youte.resources import (
    Channel,
    Channels,
    Comment,
    Comments,
    Search,
    Searches,
    Video,
    Videos,
)


def parse_search(data: SearchResult) -> Searches:
    """Parse a single page of search results from Youte.search() into a list
    of Search objects. These Search objects are like dictionaries with keys
    representing attributes of the search results.

    Parameters
    ----------
    data : dict
        A single dictionary as returned by Youte.search()

    Returns
    -------
    Searches
        A list of Search objects.
    """
    searches = [search for search in _parse_search(data)]
    return Searches(items=searches)


def parse_searches(data: Iterable[SearchResult]) -> Searches:
    """Parse a list or iterable of result pages from Youte.search() into a list of
    Search objects. Works very similarly to parse_search except over a list of search
    results.

    Parameters
    ----------
    data : Iterable[dict]
        A list or iterator of dictionaries returned by Youte.search()

    Returns
    -------
    Searches
        A list of Search objects.
    """
    searches: list[Search] = []
    for each in data:
        for search in _parse_search(each):
            searches.append(search)
    return Searches(items=searches)


def parse_video(data: VideoChannelResult) -> Videos:
    """Parse a single page of results from Youte.get_video_metadata() or
    Youte.get_most_popular() into a list of Video objects. These Video objects are
    like dictionaries with keys representing video attributes.

    Parameters
    ----------
    data : dict
        A single dictionary returned by Youte.get_video_metadata() or
        Youte.get_most_popular()

    Returns
    -------
    Videos
        A Videos object containing a list of Video objects.
    """
    videos = [video for video in _parse_video(data)]
    return Videos(items=videos)


def parse_videos(data: Iterable[VideoChannelResult]) -> Videos:
    """Parse a list or iterable of result pages from Youte.get_video_metadata() or
    Youte.get_most_popular() into a list of Video objects. These Video objects are
    like dictionaries with keys representing video attributes.

    Parameters
    ----------
    data : Iterable[dict]
        A list or iterator of dictionaries returned by Youte.get_video_metadata() or
        Youte.get_most_popular()

    Returns
    -------
    Videos
        A Videos object containing a list of Video objects.
    """
    videos: list[Video] = []
    for each in data:
        for video in _parse_video(each):
            videos.append(video)
    return Videos(items=videos)


def parse_channel(data: VideoChannelResult) -> Channels:
    """Parse a single page of results from Youte.get_channel_metadata() into a list of
    Channel objects. These Channel objects are like dictionaries with keys representing
    channel attributes.

    Parameters
    ----------
    data : dict
        A single dictionary returned by Youte.get_channel_metadata()

    Returns
    -------
    Channels
        A Channels object containing a list of Channel objects.
    """
    channels = [channel for channel in _parse_channel(data)]
    return Channels(items=channels)


def parse_channels(data: Iterable[VideoChannelResult]) -> Channels:
    """Parse an iterable of pages of results from Youte.get_channel_metadata() into a
    list of Channel objects. These Channel objects are like dictionaries with keys
    representing channel attributes.

    Parameters
    ----------
    data : Iterable[dict]
        A list or iterator of dictionaries returned by Youte.get_channel_metadata()

    Returns
    -------
    Channels
        A Channels object containing a list of Channel objects.
    """
    channels: list[Channel] = []
    for each in data:
        for channel in _parse_channel(each):
            channels.append(channel)
    return Channels(items=channels)


def parse_comment(data: StandardResult) -> Comments:
    """Parse a single page of results from Youte.get_comment_thread() or
     Youte.get_thread_replies() into a list of Comments objects. These Comment objects
     are like dictionaries with keys representing comment attributes.

    Parameters
    ----------
    data : dict
        A single dictionary returned by Youte.get_comment_thread() or
        Youte.get_thread_replies()

    Returns
    -------
    Comments
        A Comments object containing a list of Comment objects.
    """
    cmt = [cmt for cmt in _parse_comment(data)]
    return Comments(items=cmt)


def parse_comments(data: Iterable[StandardResult]) -> Comments:
    """Parse multiple pages of results from Youte.get_comment_thread() or
     Youte.get_thread_replies() into a list of Comments objects. These Comment objects
     are like dictionaries with keys representing comment attributes.

    Parameters
    ----------
    data : dict
        A list or iterator of dictionaries returned by Youte.get_comment_thread() or
        Youte.get_thread_replies()

    Returns
    -------
    Comments
        A Comments object containing a list of Comment objects.
    """
    cmts: list[Comment] = []
    for each in data:
        for cmt in _parse_comment(each):
            cmts.append(cmt)
    return Comments(items=cmts)


def _parse_search(input_: SearchResult) -> Iterator[Search]:
    if "searchListResponse" not in input_["kind"]:
        raise ValueError(
            f"Object passed to input is {input_['kind']} not a searchListResponse"
        )

    items: list[dict] = input_["items"]

    for item in items:
        snippet = item["snippet"]

        for elem in item["id"]:
            if "id" in elem or "Id" in elem:
                id_: str = item["id"][elem]

        search = Search(
            kind=item["id"]["kind"],
            id=id_,
            description=snippet["description"],
            published_at=_parse_rfc3339(snippet["publishedAt"]),
            title=html.unescape(snippet["title"]),
            thumbnail_url=snippet["thumbnails"]["high"]["url"],
            thumbnail_height=snippet["thumbnails"]["high"]["height"],
            thumbnail_width=snippet["thumbnails"]["high"]["width"],
            channel_title=snippet["channelTitle"],
            live_broadcast_content=snippet["liveBroadcastContent"],
        )

        yield search


def _parse_video(input_: VideoChannelResult) -> Iterator[Video]:
    if "videoListResponse" not in input_["kind"]:
        raise ValueError(
            f"Object passed to input is {input_['kind']} not a videoListResponse"
        )

    items: list[dict] = input_["items"]

    for item in items:
        snippet = item["snippet"]
        content_details = item["contentDetails"]
        status = item["status"]
        statistics = item["statistics"]
        topic_details = item.get("topicDetails")
        live_stream = (
            item["liveStreamingDetails"] if "liveStreamingDetails" in item else {}
        )

        search = Video(
            kind=item["kind"],
            id=item["id"],
            description=snippet["description"],
            published_at=_parse_rfc3339(snippet["publishedAt"]),
            title=snippet["title"],
            thumbnail_url=snippet["thumbnails"]["high"]["url"],
            thumbnail_height=snippet["thumbnails"]["high"]["height"],
            thumbnail_width=snippet["thumbnails"]["high"]["width"],
            channel_title=snippet["channelTitle"],
            tags=snippet["tags"],
            channel_id=snippet["channelId"],
            category_id=snippet["categoryId"],
            localized_title=snippet["localized"]["title"],
            localized_description=snippet["localized"]["description"],
            default_audio_language=snippet["defaultAudioLanguage"],
            default_language=snippet.get("defaultLanguage"),
            duration=content_details["duration"],
            dimension=content_details["dimension"],
            definition=content_details["definition"],
            caption=True if content_details["caption"] is True else False,
            licensed_content=content_details["licensedContent"],
            projection=content_details["projection"],
            upload_status=status["uploadStatus"],
            privacy_status=status["privacyStatus"],
            license=status["license"],
            embeddable=status["embeddable"],
            public_stats_viewable=status["publicStatsViewable"],
            made_for_kids=status["madeForKids"],
            view_count=statistics.get("viewCount"),
            like_count=statistics.get("likeCount"),
            comment_count=statistics.get("commentCount"),
            topic_categories=topic_details["topicCategories"]
            if topic_details
            else None,
            live_streaming_start_actual=live_stream.get("actualStartTime"),
            live_streaming_end_actual=live_stream.get("actualEndTime"),
            live_streaming_start_scheduled=live_stream.get("scheduledStartTime"),
            live_streaming_end_scheduled=live_stream.get("scheduledEndTime"),
            live_streaming_concurrent_viewers=live_stream.get("concurrentViewers"),
        )

        yield search


def _parse_channel(input_: VideoChannelResult) -> Iterator[Channel]:
    if "channelListResponse" not in input_["kind"]:
        raise ValueError("Object passed to input is not a channelListResponse")

    items: list[dict] = input_["items"]

    for item in items:
        snippet = item["snippet"]
        status = item["status"]
        statistics = item["statistics"]
        topic_details = item.get("topicDetails")
        branding = item["brandingSettings"]

        channel = Channel(
            kind=item["kind"],
            id=item["id"],
            title=snippet["title"],
            description=snippet["description"],
            custom_url=snippet["customUrl"],
            published_at=_parse_rfc3339(snippet["publishedAt"]),
            thumbnail_url=snippet["thumbnails"]["high"]["url"],
            thumbnail_height=snippet["thumbnails"]["high"]["height"],
            thumbnail_width=snippet["thumbnails"]["high"]["width"],
            default_language=snippet.get("defaultLanguage"),
            localized_title=snippet["localized"]["title"],
            localized_description=snippet["localized"]["description"],
            country=branding["channel"].get("country"),
            view_count=statistics["viewCount"],
            subscriber_count=statistics["subscriberCount"],
            video_count=statistics["videoCount"],
            hidden_subscriber_count=statistics["hiddenSubscriberCount"],
            topic_categories=topic_details["topicCategories"]
            if topic_details
            else None,
            privacy_status=status["privacyStatus"],
            is_linked=status["isLinked"],
            made_for_kids=status.get("madeForKids"),
            branding_keywords=branding["channel"].get("keywords"),
            moderated_comments=branding["channel"].get("moderatedComments"),
        )

        yield channel


def _parse_comment(input_: StandardResult) -> Iterable[Comment]:
    if "comment" not in input_["kind"]:
        raise ValueError("Object passed to input is not a comment")

    items: list[dict] = input_["items"]

    for item in items:
        can_reply: Optional[bool] = None
        total_reply_count: Optional[int] = None
        is_public: Optional[bool] = None
        if "topLevelComment" in item["snippet"]:
            snippet = item["snippet"]["topLevelComment"]["snippet"]
            can_reply = item["snippet"]["canReply"]
            total_reply_count = item["snippet"]["totalReplyCount"]
            is_public = item["snippet"]["isPublic"]
        else:
            snippet = item["snippet"]

        comment = Comment(
            id=item["id"],
            channel_id=snippet.get("channelId"),
            video_id=snippet["videoId"],
            author_display_name=snippet["authorDisplayName"],
            author_profile_image_url=snippet["authorProfileImageUrl"],
            author_channel_id=snippet["authorChannelId"]["value"],
            author_channel_url=snippet["authorChannelUrl"],
            text_display=snippet["textDisplay"],
            text_original=snippet["textOriginal"],
            parent_id=snippet.get("parentId"),
            can_rate=snippet["canRate"],
            viewer_rating=snippet["viewerRating"],
            like_count=snippet["likeCount"],
            published_at=_parse_rfc3339(snippet["publishedAt"]),
            updated_at=_parse_rfc3339(snippet["updatedAt"]),
            can_reply=can_reply,
            is_public=is_public,
            total_reply_count=total_reply_count,
        )
        yield comment


def _parse_rfc3339(string: str) -> datetime:
    """Parser function for RFC3339 datetime string returned from YouTube.
    fromisoformat() does not work with this format, except in Python 3.11
    """
    try:
        return datetime.strptime(string, "%Y-%m-%dT%H:%M:%S.%f%z")
    except ValueError:
        return datetime.strptime(string, "%Y-%m-%dT%H:%M:%S%z")
