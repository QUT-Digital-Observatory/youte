import os

import pytest

from youte.collector import Youte

API_KEY = os.environ["STAGING_API_KEY"]
NAME = "tester"


@pytest.fixture()
def yob() -> Youte:
    return Youte(api_key=API_KEY)


def test_search(yob):
    searches = [
        search for search in yob.search(query="harry potter", max_pages_retrieved=2)
    ]
    assert len(searches) == 2
    assert "items" in searches[0]
    assert len(searches[0]["items"]) > 5


def test_video_hydrate(yob):
    ids = ["4MQyV7Wluhs", "6m0qaN2sGDg"]
    videos = [vid for vid in yob.get_video_metadata(ids=ids)]
    assert len(videos)
    assert len(videos[0]["items"]) == 2


def test_channel_hydrate_ids(yob):
    ids = ["UC_NN7u1HKTQR6vurmS9iQ1A", "UCMhRG26kBpMp3GAZv5Iv7sw"]
    channels = [ch for ch in yob.get_channel_metadata(ids=ids)]
    assert len(channels)
    assert len(channels[0]["items"]) == 2


# def test_channel_hydrate_username(yob):
#     usernames = ["@brilliantclassics", "@TED"]
#     channels = [ch
#                 for ch in
#                 yob.get_channel_metadata(usernames=usernames)]
#     print(channels)
#     assert len(channels)
#     assert len(channels[0]["items"]) == 2


def test_comments_by_videos(yob):
    vid_ids = ["4MQyV7Wluhs", "6m0qaN2sGDg"]
    channel_ids = ["UC_NN7u1HKTQR6vurmS9iQ1A", "UCMhRG26kBpMp3GAZv5Iv7sw"]
    comments = [cmt for cmt in yob.get_comment_threads(video_ids=vid_ids)]
    assert len(comments) > 2
    assert len(comments[0]["items"]) > 50


def test_comments_by_channels(yob):
    channel_id = ["UC_NN7u1HKTQR6vurmS9iQ1A"]
    comments = [cmt for cmt in yob.get_comment_threads(related_channel_ids=channel_id)]
    assert len(comments)
    assert len(comments[0]["items"]) > 50


def test_comments_by_id(yob):
    cmt_ids = ["Ugxk_z1g6ZmYZ9-ldXF4AaABAg", "UgyXx-EYT7oYvqwp_bJ4AaABAg"]
    comments = [cmt for cmt in yob.get_comment_threads(comment_ids=cmt_ids)]
    assert len(comments)
    assert len(comments[0]["items"]) == 2


def test_comment_fail(yob):
    vid_ids = ["4MQyV7Wluhs", "6m0qaN2sGDg"]
    channel_ids = ["UC_NN7u1HKTQR6vurmS9iQ1A", "UCMhRG26kBpMp3GAZv5Iv7sw"]
    with pytest.raises(ValueError):
        comments = [
            cmt
            for cmt in yob.get_comment_threads(
                video_ids=vid_ids, related_channel_ids=channel_ids
            )
        ]


def test_replies(yob: Youte):
    thread_ids = ["UgzZ1346QJnRezL5qgt4AaABAg", "Ugxsacik4CLIVA83S-B4AaABAg"]
    comments = [
        cmt
        for cmt in yob.get_thread_replies(
            thread_ids=thread_ids, text_format="plainText"
        )
    ]
    assert len(comments)
    assert len(comments[0]["items"]) > 2


def test_most_popular(yob: Youte):
    videos = [vid for vid in yob.get_most_popular()]
    assert len(videos)
    assert len(videos[0]["items"]) > 10


def test_related_videos(yob: Youte):
    vid_ids = ["4MQyV7Wluhs", "6m0qaN2sGDg"]
    videos = [
        vid for vid in yob.get_related_videos(video_ids=vid_ids, max_pages_retrieved=2)
    ]
    assert len(videos)
    assert "related_to_video_id" in videos[0]
    assert videos[0]["related_to_video_id"] == vid_ids[0]  # type: ignore
    assert len(videos[0]["items"]) > 10
