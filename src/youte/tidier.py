import sqlite3
import html
import json
from typing import Iterable, Mapping, Union
import re
from tqdm import tqdm
import logging
from pathlib import Path

from youte.utilities import validate_file, check_file_overwrite
import youte.table_mappings as mappings

logger = logging.getLogger()


def connect_db(db_path: Union[str, Path]) -> sqlite3.Connection:
    """Helper function for opening DB connections with standard config set."""
    return sqlite3.connect(db_path, isolation_level=None)


def master_tidy(filepath: str, output: Union[str, Path]) -> None:
    output = check_file_overwrite(validate_file(output, suffix=".db"))

    with open(filepath, mode="r") as file:
        first_response = json.loads(file.readline())
        kind = first_response["kind"]

    if "video" in kind:
        logger.info(f"{kind}")
        tidy_video(filepath, output)
    elif "channel" in kind:
        tidy_channel(filepath, output)
    elif "comment" in kind:
        tidy_comments(filepath, output)
    elif "search" in kind:
        tidy_search(filepath, output)


def _get_items(filepath: str) -> Iterable:
    with open(filepath, mode="r") as file:
        responses = (row.rstrip() for row in file.readlines())
        for response in responses:
            try:
                items = json.loads(response)["items"]
                for item in items:
                    yield item
            except KeyError:
                logger.warning("No items found in JSON response")


def _unnest_map(filepath: Mapping) -> Iterable:
    for key, value in filepath.items():
        if isinstance(value, Mapping):
            yield from _annotate_key(value, name=key)
        else:
            yield key, value


def _annotate_key(filepath, name):
    for key, value in filepath.items():
        if isinstance(value, Mapping):
            yield from _annotate_key(value, name=key)
        else:
            yield f"{name}_{key}", value


def _normalise_name(string):
    pattern = re.compile(r"([A-Z])")
    new_string = re.sub(pattern, r"_\1", string)
    return new_string.lower()


def tidy_search(filepath: str, output: Union[str, Path]) -> None:
    db = connect_db(output)

    db.execute("begin")

    db.execute(
        """
        CREATE TABLE IF NOT EXISTS search_results(
             id primary key,
             kind,
             published_at,
             title,
             description,
             thumbnails,
             channel_title,
             channel_id,
             live_broadcast_content
             );
        """
    )

    items = _get_items(filepath=filepath)

    for item in tqdm(items):
        kind = item["id"]["kind"]
        video_id = item["id"]["videoId"]
        snippet = item["snippet"]
        channel_id = snippet["channelId"]
        published_at = snippet["publishedAt"]
        title = html.unescape(snippet["title"])
        description = snippet["description"]
        thumbnail = json.dumps(snippet["thumbnails"])
        channel_title = snippet["channelTitle"]
        live_broadcast_content = snippet["liveBroadcastContent"]

        db.execute(
            """
                    REPLACE INTO search_results
                    VALUES (?,?,?,?,?,?,?,?,?)
                    """,
            (
                video_id,
                kind,
                published_at,
                title,
                description,
                thumbnail,
                channel_title,
                channel_id,
                live_broadcast_content,
            ),
        )

    db.execute("commit")

    db.close()


def tidy_video(filepath: str, output: Union[str, Path]) -> None:
    db = connect_db(output)

    db.execute("begin")

    db.execute(mappings.video_sql_table["create"])

    items = _get_items(filepath=filepath)
    for item in tqdm(items):
        video_mapping = {}

        snippet = item["snippet"]
        content_details = item["contentDetails"]
        status = item["status"]
        statistics = item["statistics"]
        topic_details = item.get("topicDetails")
        content_rating = content_details["contentRating"]
        recording = item["recordingDetails"]
        region_restriction = content_details.get("regionRestriction")

        video_mapping["video_id"] = item["id"]
        video_mapping["published_at"] = snippet["publishedAt"]
        video_mapping["channel_id"] = snippet["channelId"]
        video_mapping["title"] = snippet["title"]
        video_mapping["description"] = snippet["description"]
        video_mapping["thumbnails"] = json.dumps(snippet["thumbnails"])
        video_mapping["channel_title"] = snippet["channelTitle"]
        video_mapping["category_id"] = snippet["categoryId"]
        video_mapping["live_broadcast_content"] = snippet["liveBroadcastContent"]
        video_mapping["localized_title"] = snippet["localized"]["title"]
        video_mapping["localized_description"] = snippet["localized"]["description"]
        video_mapping["duration"] = content_details["duration"]
        video_mapping["dimension"] = content_details["dimension"]
        video_mapping["definition"] = content_details["definition"]
        video_mapping["caption"] = content_details["caption"]
        video_mapping["licensed_content"] = content_details["licensedContent"]
        video_mapping["upload_status"] = status["uploadStatus"]
        video_mapping["privacy_status"] = status["privacyStatus"]
        video_mapping["license"] = status["license"]
        video_mapping["public_stats_viewable"] = status["publicStatsViewable"]
        video_mapping["made_for_kids"] = status["madeForKids"]

        # optional properties
        video_mapping["default_language"] = snippet.get("defaultLanguage")
        video_mapping["default_audio_language"] = snippet.get("defaultAudioLanguage")
        video_mapping["rejection_reason"] = status.get("rejectionReason")
        video_mapping["region_allowed"] = (
            str(region_restriction.get("allowed")) if region_restriction else None
        )
        video_mapping["region_blocked"] = (
            str(region_restriction.get("blocked")) if region_restriction else None
        )
        video_mapping["yt_rating"] = content_rating.get("ytRating")
        video_mapping["tags"] = str(snippet.get("tags"))
        video_mapping["view_count"] = statistics.get("viewCount")
        video_mapping["like_count"] = statistics.get("likeCount")
        video_mapping["comment_count"] = statistics.get("commentCount")
        video_mapping["topic_categories"] = (
            str(topic_details["topicCategories"]) if topic_details else None
        )
        video_mapping["recording_location"] = str(recording.get("location"))

        db.execute(mappings.video_sql_table["insert"], video_mapping)

        db.execute("commit")

    db.close()


def tidy_channel(filepath: str, output: Union[str, Path]) -> None:
    db = connect_db(output)

    db.execute("begin")
    db.execute(mappings.channel_sql_table["create"])

    items = _get_items(filepath=filepath)
    for item in tqdm(items):
        channel_mapping = {}

        snippet = item["snippet"]
        content_details = item["contentDetails"]
        related_playlists = content_details.get("relatedPlaylists")
        status = item["status"]
        statistics = item["statistics"]
        topic_details = item.get("topicDetails")
        branding = item.get("brandingSettings")
        owner = item["contentOwnerDetails"]

        channel_mapping["channel_id"] = item["id"]
        channel_mapping["title"] = snippet["title"]
        channel_mapping["description"] = snippet["description"]
        channel_mapping["published_at"] = snippet["publishedAt"]
        channel_mapping["custom_url"] = snippet.get("customUrl")
        channel_mapping["thumbnails"] = json.dumps(snippet["thumbnails"])
        channel_mapping["default_language"] = snippet.get("defaultLanguage")
        channel_mapping["country"] = snippet.get("country")
        channel_mapping["localized_title"] = snippet["localized"]["title"]
        channel_mapping["localized_description"] = snippet["localized"]["description"]
        channel_mapping["related_playlists_likes"] = (
            related_playlists.get("likes") if related_playlists else None
        )
        channel_mapping["related_playlists_uploads"] = (
            related_playlists.get("uploads") if related_playlists else None
        )
        channel_mapping["view_count"] = statistics.get("viewCount")
        channel_mapping["subscriber_count"] = statistics.get("subscriberCount")
        channel_mapping["video_count"] = statistics.get("videoCount")
        channel_mapping["hidden_subscriber_count"] = statistics["hiddenSubscriberCount"]
        channel_mapping["topic_ids"] = (
            str(topic_details.get("topicIds")) if topic_details else None
        )
        channel_mapping["topic_categories"] = (
            str(topic_details.get("topicCategories")) if topic_details else None
        )
        channel_mapping["privacy_status"] = status["privacyStatus"]
        channel_mapping["is_linked"] = status.get("isLinked")
        channel_mapping["made_for_kids"] = status.get("madeForKids")
        channel_mapping["keywords"] = branding["channel"].get("keywords")
        channel_mapping["moderate_comments"] = branding["channel"].get(
            "moderateComments"
        )
        channel_mapping["unsubscribed_trailer"] = branding["channel"].get(
            "unsubscribedTrailer"
        )
        channel_mapping["content_owner"] = owner.get("contentOwner")
        channel_mapping["time_linked"] = owner.get("timeLinked")

        db.execute(mappings.channel_sql_table["insert"], channel_mapping)

    db.execute("commit")

    db.close()


def tidy_comments(filepath, output: Union[str, Path]) -> None:
    db = connect_db(output)

    db.execute("begin")
    db.execute(mappings.comment_sql_table["create"])

    items = _get_items(filepath=filepath)
    for item in tqdm(items):
        comment_mapping = {}

        if "topLevelComment" in item["snippet"]:
            snippet = item["snippet"]["topLevelComment"]["snippet"]
            comment_mapping["reply_count"] = item["snippet"].get("totalReplyCount")
            comment_mapping["can_reply"] = item["snippet"].get("canReply")
        else:
            comment_mapping["reply_count"] = None
            comment_mapping["can_reply"] = None
            snippet = item["snippet"]

        comment_mapping["comment_id"] = item["id"]
        comment_mapping["video_id"] = snippet.get("videoId")
        comment_mapping["channel_id"] = snippet.get("channelId")
        comment_mapping["parent_id"] = snippet.get("parentId")
        comment_mapping["text_display"] = html.unescape(snippet["textDisplay"])
        comment_mapping["text_original"] = snippet["textOriginal"]
        comment_mapping["author_name"] = snippet["authorDisplayName"]
        comment_mapping["author_channel_url"] = snippet["authorChannelUrl"]
        comment_mapping["author_channel_id"] = snippet["authorChannelId"]["value"]
        comment_mapping["can_rate"] = snippet["canRate"]
        comment_mapping["viewer_rating"] = snippet["viewerRating"]
        comment_mapping["like_count"] = snippet["likeCount"]
        comment_mapping["published_at"] = snippet["publishedAt"]
        comment_mapping["updated_at"] = snippet["updatedAt"]

        db.execute(mappings.comment_sql_table["insert"], comment_mapping)

    db.execute("commit")

    db.close()
