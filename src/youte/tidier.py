import csv
import html
import json
import logging
import re
import sqlite3
from pathlib import Path
from typing import Iterable, Mapping, Sequence, Union

import click
from tqdm import tqdm

import youte.table_mappings as mappings

logger = logging.getLogger()


def connect_db(db_path: Union[str, Path]) -> sqlite3.Connection:
    """Helper function for opening DB connections with standard config set."""
    return sqlite3.connect(db_path, isolation_level=None)


def master_tidy(filepath: str, output: Union[str, Path]) -> None:
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


def get_items(filepath: str) -> Iterable[dict]:
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

    db.execute("BEGIN")
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
    items = get_items(filepath=filepath)
    total = 0

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

        total += 1

    db.execute("commit")

    db.close()
    click.echo(f"{total} items processed.")
    click.echo(f"Data stored in {output} in `search_results` table.")


def _get_mapping(item: dict, resource_kind) -> dict:
    valid_kinds = ["search", "channels", "videos", "comments"]

    if resource_kind not in valid_kinds:
        raise ValueError(f"resource_kind must be one of {str(valid_kinds)}")

    mapping = dict()

    if resource_kind == "search":
        mapping["kind"] = item["id"]["kind"]
        for elem in item["id"]:
            if "id" in elem or "Id" in elem:
                mapping["id"] = item["id"][elem]
        snippet = item["snippet"]
        mapping["channel_id"] = snippet["channelId"]
        mapping["published_at"] = snippet["publishedAt"]
        mapping["title"] = html.unescape(snippet["title"])
        mapping["description"] = snippet["description"]
        mapping["thumbnail"] = json.dumps(snippet["thumbnails"])
        mapping["channel_title"] = snippet["channelTitle"]
        mapping["live_broadcast_content"] = snippet["liveBroadcastContent"]

    if resource_kind == "comments":
        if "topLevelComment" in item["snippet"]:
            snippet = item["snippet"]["topLevelComment"]["snippet"]
            mapping["reply_count"] = item["snippet"].get("totalReplyCount")
            mapping["can_reply"] = item["snippet"].get("canReply")
        else:
            mapping["reply_count"] = None
            mapping["can_reply"] = None
            snippet = item["snippet"]

        mapping["comment_id"] = item["id"]
        mapping["video_id"] = snippet.get("videoId")
        mapping["channel_id"] = snippet.get("channelId")
        mapping["parent_id"] = snippet.get("parentId")
        mapping["text_display"] = html.unescape(snippet["textDisplay"])
        mapping["text_original"] = snippet["textOriginal"]
        mapping["author_name"] = snippet["authorDisplayName"]
        mapping["author_channel_url"] = snippet["authorChannelUrl"]
        mapping["author_channel_id"] = snippet["authorChannelId"]["value"]
        mapping["can_rate"] = snippet["canRate"]
        mapping["viewer_rating"] = snippet["viewerRating"]
        mapping["like_count"] = snippet["likeCount"]
        mapping["published_at"] = snippet["publishedAt"]
        mapping["updated_at"] = snippet["updatedAt"]

    if resource_kind == "videos":
        snippet = item["snippet"]
        content_details = item["contentDetails"]
        status = item["status"]
        statistics = item["statistics"]
        topic_details = item.get("topicDetails")
        content_rating = content_details["contentRating"]
        recording = item["recordingDetails"]
        region_restriction = content_details.get("regionRestriction")

        mapping["video_id"] = item["id"]
        mapping["published_at"] = snippet["publishedAt"]
        mapping["channel_id"] = snippet["channelId"]
        mapping["title"] = snippet["title"]
        mapping["description"] = snippet["description"]
        mapping["thumbnails"] = json.dumps(snippet["thumbnails"])
        mapping["channel_title"] = snippet["channelTitle"]
        mapping["category_id"] = snippet["categoryId"]
        mapping["live_broadcast_content"] = snippet["liveBroadcastContent"]
        mapping["localized_title"] = snippet["localized"]["title"]
        mapping["localized_description"] = snippet["localized"]["description"]
        mapping["duration"] = content_details["duration"]
        mapping["dimension"] = content_details["dimension"]
        mapping["definition"] = content_details["definition"]
        mapping["caption"] = content_details["caption"]
        mapping["licensed_content"] = content_details["licensedContent"]
        mapping["upload_status"] = status["uploadStatus"]
        mapping["privacy_status"] = status["privacyStatus"]
        mapping["license"] = status["license"]
        mapping["public_stats_viewable"] = status["publicStatsViewable"]
        mapping["made_for_kids"] = status["madeForKids"]

        # optional properties
        mapping["default_language"] = snippet.get("defaultLanguage")
        mapping["default_audio_language"] = snippet.get("defaultAudioLanguage")
        mapping["rejection_reason"] = status.get("rejectionReason")
        mapping["region_allowed"] = (
            str(region_restriction.get("allowed")) if region_restriction else None
        )
        mapping["region_blocked"] = (
            str(region_restriction.get("blocked")) if region_restriction else None
        )
        mapping["yt_rating"] = content_rating.get("ytRating")
        mapping["tags"] = str(snippet.get("tags"))
        mapping["view_count"] = statistics.get("viewCount")
        mapping["like_count"] = statistics.get("likeCount")
        mapping["comment_count"] = statistics.get("commentCount")
        mapping["topic_categories"] = (
            str(topic_details["topicCategories"]) if topic_details else None
        )
        mapping["recording_location"] = str(recording.get("location"))

    if resource_kind == "channels":
        snippet = item["snippet"]
        content_details = item["contentDetails"]
        related_playlists = content_details.get("relatedPlaylists")
        status = item["status"]
        statistics = item["statistics"]
        topic_details = item.get("topicDetails")
        branding = item.get("brandingSettings")
        owner = item["contentOwnerDetails"]

        mapping["channel_id"] = item["id"]
        mapping["title"] = snippet["title"]
        mapping["description"] = snippet["description"]
        mapping["published_at"] = snippet["publishedAt"]
        mapping["custom_url"] = snippet.get("customUrl")
        mapping["thumbnails"] = json.dumps(snippet["thumbnails"])
        mapping["default_language"] = snippet.get("defaultLanguage")
        mapping["country"] = snippet.get("country")
        mapping["localized_title"] = snippet["localized"]["title"]
        mapping["localized_description"] = snippet["localized"]["description"]
        mapping["related_playlists_likes"] = (
            related_playlists.get("likes") if related_playlists else None
        )
        mapping["related_playlists_uploads"] = (
            related_playlists.get("uploads") if related_playlists else None
        )
        mapping["view_count"] = statistics.get("viewCount")
        mapping["subscriber_count"] = statistics.get("subscriberCount")
        mapping["video_count"] = statistics.get("videoCount")
        mapping["hidden_subscriber_count"] = statistics["hiddenSubscriberCount"]
        mapping["topic_ids"] = (
            str(topic_details.get("topicIds")) if topic_details else None
        )
        mapping["topic_categories"] = (
            str(topic_details.get("topicCategories")) if topic_details else None
        )
        mapping["privacy_status"] = status["privacyStatus"]
        mapping["is_linked"] = status.get("isLinked")
        mapping["made_for_kids"] = status.get("madeForKids")
        mapping["keywords"] = branding["channel"].get("keywords")
        mapping["moderate_comments"] = branding["channel"].get("moderateComments")
        mapping["unsubscribed_trailer"] = branding["channel"].get("unsubscribedTrailer")
        mapping["content_owner"] = owner.get("contentOwner")
        mapping["time_linked"] = owner.get("timeLinked")

    return mapping


def _write_csv(source: Sequence[Mapping], outfile: Union[str, Path]) -> None:
    fieldnames = source[0].keys()

    with open(outfile, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        if f.tell() == 0:
            writer.writeheader()
        writer.writerows(source)


def tidy_to_csv(
    items: Iterable[Mapping], output: Union[str, Path], resource_kind: str
) -> None:
    to_write = []

    for item in tqdm(items):
        mapping = _get_mapping(item, resource_kind=resource_kind)
        to_write.append(mapping)

    _write_csv(source=to_write, outfile=output)


def tidy_video(filepath: str, output: Union[str, Path]) -> None:
    db = connect_db(output)

    db.execute("begin")
    db.execute(mappings.VIDEO_SQL_TABLE["create"])
    db.execute("commit")

    items = get_items(filepath=filepath)
    total = 0

    for item in tqdm(items):
        video_mapping = _get_mapping(item, "videos")

        db.execute("BEGIN")
        db.execute(mappings.VIDEO_SQL_TABLE["insert"], video_mapping)
        db.execute("COMMIT")

        total += 1

    db.close()
    click.echo(f"{total} items processed.")
    click.echo(f"Data stored in {output} in `videos` table.")


def tidy_channel(filepath: str, output: Union[str, Path]) -> None:
    db = connect_db(output)

    db.execute("begin")
    db.execute(mappings.CHANNEL_SQL_TABLE["create"])
    db.execute("commit")

    items = get_items(filepath=filepath)
    total = 0

    for item in tqdm(items):
        channel_mapping = _get_mapping(item, "channels")

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

        db.execute("begin")
        db.execute(mappings.CHANNEL_SQL_TABLE["insert"], channel_mapping)
        db.execute("commit")

        total += 1

    db.close()
    click.echo(f"{total} items processed.")
    click.echo(f"Data stored in {output} in `channels` table.")


def tidy_comments(filepath, output: Union[str, Path]) -> None:
    db = connect_db(output)

    db.execute("begin")
    db.execute(mappings.COMMENT_SQL_TABLE["create"])
    db.execute("commit")

    items = get_items(filepath=filepath)
    total = 0

    for item in tqdm(items):
        comment_mapping = _get_mapping(item, "comments")

        db.execute("BEGIN")
        db.execute(mappings.COMMENT_SQL_TABLE["insert"], comment_mapping)
        db.execute("COMMIT")

        total += 1

    db.close()
    click.echo(f"{total} items processed.")
    click.echo(f"Data stored in {output} in `comments` table.")


def get_id(items: Iterable[dict]) -> Iterable[str]:
    for item in items:
        id_ = item["id"]
        if isinstance(id_, dict):
            for elem in id_:
                if "id" in elem or "Id" in elem:
                    id_ = id_[elem]
        yield id_
