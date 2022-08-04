import sqlite3
import html
import json
from typing import Iterable, Mapping
import re
from tqdm import tqdm

from youtupy.utilities import validate_file, check_file_overwrite
from youtupy.table_mappings import video_sql_tables


def _get_items(input) -> Iterable:
    with open(input, mode='r') as file:
        responses = (row.rstrip() for row in file.readlines())
        for response in responses:
            items = json.loads(response)['items']
            for item in items:
                yield item


def _unnest_map(input: Mapping) -> Iterable:
    for key, value in input.items():
        if isinstance(value, Mapping):
            yield from _annotate_key(value, name=key)
        else:
            yield key, value


def _annotate_key(input, name):
    for key, value in input.items():
        if isinstance(value, Mapping):
            yield from _annotate_key(value, name=key)
        else:
            yield f'{name}_{key}', value


def _normalise_name(string):
    pattern = re.compile(r'([A-Z])')
    new_string = re.sub(pattern, r'_\1', string)
    return new_string.lower()


def tidy_search(input: str, output: str) -> None:
    output = check_file_overwrite(validate_file(output, suffix='.db'))
    db = sqlite3.connect(output)
    with db:
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS search_results(
                 id primary key,
                 kind,
                 published_at,
                 title,
                 description,
                 thumbnail_url,
                 thumbnail_width,
                 thumbnail_height,
                 channel_title,
                 channel_id,
                 playlist_id,
                 live_broadcast_content
                 );
            """
        )

    items = _get_items(input=input)

    for item in items:
        kind = item['id']['kind']
        video_id = item['id']['videoId']
        channel_id = item['id']['channelId']
        playlist_id = item['id']['playlistId']
        snippet = item['snippet']
        published_at = snippet['publishedAt']
        title = html.unescape(snippet['title'])
        description = snippet['description']
        thumbnail_url = snippet['thumbnails']['url']
        thumbnail_width = snippet['thumbnails']['width']
        thumbnail_height = snippet['thumbnails']['height']
        channel_title = snippet['channelTitle']
        live_broadcast_content = snippet['liveBroadcastContent']

        db.execute(
            """
                    REPLACE INTO search_results
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
                    """,
            (video_id,
             kind,
             published_at,
             title,
             description,
             thumbnail_url,
             thumbnail_width,
             thumbnail_height,
             channel_title,
             channel_id,
             playlist_id,
             live_broadcast_content)
        )
        db.commit()

    db.close()


def tidy_video(input: str, output: str) -> None:
    output = check_file_overwrite(validate_file(output, suffix='.db'))
    db = sqlite3.connect(output)

    db.execute(video_sql_tables['create'])

    items = _get_items(input=input)
    for item in tqdm(items):
        video_mapping = {}

        snippet = item['snippet']
        content_details = item['contentDetails']
        status = item['status']
        statistics = item['statistics']
        topic_details = item.get('topicDetails')
        content_rating = content_details['contentRating']
        recording = item['recordingDetails']
        region_restriction = content_details.get('regionRestriction')

        video_mapping['video_id'] = item['id']
        video_mapping['published_at'] = snippet['publishedAt']
        video_mapping['channel_id'] = snippet['channelId']
        video_mapping['title'] = snippet['title']
        video_mapping['description'] = snippet['description']
        video_mapping['thumbnails'] = json.dumps(snippet['thumbnails'])
        video_mapping['channel_title'] = snippet['channelTitle']
        video_mapping['tags'] = str(snippet.get('tags'))
        video_mapping['category_id'] = snippet['categoryId']
        video_mapping['live_broadcast_content'] = snippet[
            'liveBroadcastContent']
        video_mapping['default_language'] = snippet.get('defaultLanguage')
        video_mapping['localized_title'] = snippet['localized']['title']
        video_mapping['localized_description'] = snippet['localized'][
            'description']
        video_mapping['default_audio_language'] = snippet.get(
            'defaultAudioLanguage')
        video_mapping['duration'] = content_details['duration']
        video_mapping['dimension'] = content_details['dimension']
        video_mapping['definition'] = content_details['definition']
        video_mapping['caption'] = content_details['caption']
        video_mapping['licensed_content'] = content_details['licensedContent']
        video_mapping['region_allowed'] = str(region_restriction.get('allowed')) \
            if region_restriction else None
        video_mapping['region_blocked'] = str(region_restriction.get('blocked')) \
            if region_restriction else None
        video_mapping['yt_rating'] = content_rating.get('ytRating')
        video_mapping['upload_status'] = status['uploadStatus']
        video_mapping['rejection_reason'] = status.get('rejectionReason')
        video_mapping['privacy_status'] = status['privacyStatus']
        video_mapping['license'] = status['license']
        video_mapping['public_stats_viewable'] = status['publicStatsViewable']
        video_mapping['made_for_kids'] = status['madeForKids']
        video_mapping['view_count'] = statistics.get('viewCount')
        video_mapping['like_count'] = statistics.get('likeCount')
        video_mapping['comment_count'] = statistics.get('commentCount')
        video_mapping['topic_categories'] = str(
            topic_details['topicCategories']) if topic_details else None
        video_mapping['recording_location'] = str(recording.get('location'))

        db.execute(video_sql_tables['insert'], video_mapping)
        db.commit()

    db.close()


def process_to_database(source, dbpath: str):
    db = sqlite3.connect(dbpath)
    schema = f"{source}_results" if source == 'search' else f"{source}s"

    if source == 'search':
        api_responses = db.execute("""
                SELECT response
                FROM search_api_response
                WHERE response NOTNULL
                """)

        for api_response in api_responses:
            items = json.loads(api_response[0])['items']

            for item in items:
                video_id = item['id']['videoId']
                published_at = item['snippet']['publishedAt']
                channel_id = item['snippet']['channelId']
                title = html.unescape(item['snippet']['title'])
                description = item['snippet']['description']
                channel_title = item['snippet']['channelTitle']

                with db:
                    db.execute(
                        f"""
                        INSERT OR IGNORE INTO
                        {schema}(video_id, published_at, channel_id,
                                       title, description, channel_title)
                        values (?,?,?,?,?,?)
                        """,
                        (video_id, published_at, channel_id,
                         title, description, channel_title)
                    )

    elif source == 'video':
        api_responses = db.execute(
            """
            SELECT video_id, response
            FROM video_api_response
            WHERE response NOTNULL
            """)

        for api_response in api_responses:
            video_id = api_response[0]
            item = json.loads(api_response[1])

            published_at = item['snippet']['publishedAt']
            channel_id = item['snippet']['channelId']
            title = item['snippet']['title']
            description = item['snippet']['description']
            channel_title = item['snippet']['channelTitle']
            if item.get('topicDetails'):
                topic_categories = item['topicDetails'].get('topicCategories')
            else:
                topic_categories = None

            if item.get('status'):
                upload_status = item['status'].get('uploadStatus')
            else:
                upload_status = None

            if item.get('statistics'):
                view_count = item['statistics'].get('viewCount')
                like_count = item['statistics'].get('likeCount')
                comment_count = item['statistics'].get('commentCount')

            with db:
                db.execute(
                    """
                    INSERT OR REPLACE INTO videos
                    VALUES (?,?,?,?,?,?,?,?,?,?,?)
                    """,
                    (video_id, published_at, channel_id, title, description,
                     channel_title, str(topic_categories), upload_status,
                     view_count, like_count, comment_count))

    elif source == 'channel':
        api_responses = db.execute(
            """
            SELECT channel_id, response
            FROM channel_api_response
            WHERE response NOTNULL
            """)

        for api_response in api_responses:
            channel_id = api_response[0]
            item = json.loads(api_response[1])

            ch_published_at = item['snippet']['publishedAt']
            ch_title = item['snippet']['title']
            ch_description = item['snippet']['description']

            if item.get('topicDetails'):
                ch_topic_categories = item['topicDetails'].get(
                    'topicCategories')
            else:
                ch_topic_categories = None

            if item.get('statistics'):
                ch_view_count = item['statistics'].get('viewCount')
                ch_subscriber_count = item['statistics'].get('subscriberCount')
                ch_video_count = item['statistics'].get('videoCount')

            with db:
                db.execute(
                    """
                    INSERT OR REPLACE INTO channels
                    VALUES (?,?,?,?,?,?,?,?)
                    """,
                    (channel_id, ch_published_at, ch_title, ch_description,
                     str(ch_topic_categories),
                     ch_view_count, ch_subscriber_count, ch_video_count))

    elif source == 'comment_thread':
        api_responses = db.execute(
            """
            SELECT response
            FROM comment_threads_api_response
            WHERE response NOTNULL
            """
        )

        for api_response in api_responses:
            items = json.loads(api_response[0])['items']

            for item in items:
                thread_id = item['id']
                video_id = item['snippet']['videoId']
                can_reply = item['snippet']['canReply']
                reply_count = item['snippet']['totalReplyCount']

                snippet = item['snippet']['topLevelComment']['snippet']
                text_display = snippet['textDisplay']
                text_original = snippet['textOriginal']
                author_name = snippet['authorDisplayName']
                author_url = snippet['authorChannelUrl']
                author_channel_id = snippet['authorChannelId']['value']
                can_rate = snippet['canRate']
                viewer_rating = snippet['viewerRating']
                like_count = snippet['likeCount']
                published_at = snippet['publishedAt']
                updated_at = snippet['updatedAt']

                with db:
                    db.execute(
                        """
                        CREATE TABLE IF NOT EXISTS comment_threads(
                            thread_id PRIMARY KEY,
                            video_id,
                            can_reply,
                            reply_count,
                            text_display,
                            text_original,
                            author_name,
                            author_url,
                            author_channel_id,
                            can_rate,
                            viewer_rating,
                            like_count,
                            published_at,
                            updated_at
                            )
                        """
                    )

                    db.execute(
                        """
                        INSERT OR REPLACE INTO comment_threads
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                        """,
                        (thread_id,
                         video_id,
                         can_reply,
                         reply_count,
                         html.unescape(text_display),
                         text_original,
                         author_name,
                         author_url,
                         author_channel_id,
                         can_rate,
                         viewer_rating,
                         like_count,
                         published_at,
                         updated_at)
                    )

    elif source == 'reply':
        api_responses = db.execute(
            """
            SELECT response
            FROM reply_api_response
            WHERE response NOTNULL
            """
        )

        for api_response in api_responses:
            items = json.loads(api_response[0])['items']

            for item in items:
                reply_id = item['id']

                snippet = item['snippet']
                text_display = snippet['textDisplay']
                text_original = snippet['textOriginal']
                parent_id = snippet['parentId']
                author_name = snippet['authorDisplayName']
                author_url = snippet['authorChannelUrl']
                author_channel_id = snippet['authorChannelId']['value']
                can_rate = snippet['canRate']
                viewer_rating = snippet['viewerRating']
                like_count = snippet['likeCount']
                published_at = snippet['publishedAt']
                updated_at = snippet['updatedAt']

                with db:
                    db.execute(
                        """
                        CREATE TABLE IF NOT EXISTS replies(
                            reply_id PRIMARY KEY,
                            reply_text_display,
                            reply_text_original,
                            parent_id,
                            author_name,
                            author_url,
                            author_channel_id,
                            can_rate,
                            viewer_rating,
                            like_count,
                            published_at,
                            updated_at
                            )
                        """
                    )

                    db.execute(
                        """
                        INSERT OR REPLACE INTO replies
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
                        """,
                        (reply_id,
                         html.unescape(text_display),
                         text_original,
                         parent_id,
                         author_name,
                         author_url,
                         author_channel_id,
                         can_rate,
                         viewer_rating,
                         like_count,
                         published_at,
                         updated_at)
                    )
