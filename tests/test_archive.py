import os

from sqlalchemy import func
from sqlalchemy.engine import Engine

from youte import database, parser
from youte.collector import Youte
from youte.resources import Channels, Comments, Searches, Videos

API_KEY = os.environ["STAGING_API_KEY"]


def test_create_tables(path="test.db"):
    engine = database.set_up_database(path)
    assert os.path.exists(path)
    assert isinstance(engine, Engine)
    os.remove(path)


def test_full_archive():
    search_query = "stoicism"
    yob = Youte(api_key=API_KEY)
    engine = database.set_up_database("test.db")

    s_results = [
        result
        for result in yob.search(search_query, max_result=10, max_pages_retrieved=2)
    ]
    assert len(s_results) == 2

    searches = parser.parse_searches(s_results)
    assert isinstance(searches, Searches)
    assert len(searches.items) > 10

    video_ids = [s.id for s in searches.items]
    channel_ids = [c.channel_id for c in searches.items]

    v_results = [r for r in yob.get_video_metadata(video_ids)]
    assert len(v_results) > 0

    videos = parser.parse_videos(v_results)
    assert isinstance(videos, Videos)
    assert len(videos.items) > 10

    c_results = [r for r in yob.get_channel_metadata(channel_ids)]
    assert len(c_results) > 0

    channels = parser.parse_channels(c_results)
    assert isinstance(channels, Channels)
    assert len(channels.items) > 5

    ids_for_comments = [v.id for v in videos.items if v.comment_count < 200]
    if len(ids_for_comments) > 5:
        ids_for_comments = ids_for_comments[:5]
    cmt_results = [r for r in yob.get_comment_threads(video_ids=ids_for_comments)]
    assert len(cmt_results) > 0

    comments = parser.parse_comments(cmt_results)
    assert isinstance(comments, Comments)
    assert len(comments.items) > 5

    thread_ids = [t.id for t in comments.items if t.total_reply_count > 0]
    if len(thread_ids) > 10:
        thread_ids = thread_ids[:10]
    r_results = [r for r in yob.get_thread_replies(thread_ids)]
    replies = parser.parse_comments(r_results)
    assert isinstance(replies, Comments)
    assert len(replies.items) > 0

    database.populate_searches(engine, [searches])
    database.populate_videos(engine, [videos])
    database.populate_channels(engine, [channels])
    database.populate_comments(engine, [comments, replies])

    with engine.connect() as conn:
        search_count = conn.execute(func.count(database.Search.id))
        assert search_count.all()[0][0] > 10

        video_count = conn.execute(func.count(database.Video.id))
        assert video_count.all()[0][0] > 10

        channel_count = conn.execute(func.count(database.Channel.id))
        assert channel_count.all()[0][0] > 10

        cmt_count = conn.execute(func.count(database.Comment.id))
        assert cmt_count.all()[0][0] > 10
