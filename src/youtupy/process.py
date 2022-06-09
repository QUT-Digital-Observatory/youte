import sqlite3
import html
import json


def process_to_database(source: ['search', 'video', 'channel'], dbpath: str):
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


