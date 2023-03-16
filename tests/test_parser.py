import json
import os

import pytest

from youte.collector import Youte
from youte.parser import (
    parse_channel,
    parse_channels,
    parse_comment,
    parse_comments,
    parse_search,
    parse_searches,
    parse_video,
    parse_videos,
)
from youte.resources import Channels, Comments, Searches, Videos

API_KEY = os.environ["STAGING_API_KEY"]
NAME = "tester"


@pytest.fixture()
def yob() -> Youte:
    return Youte(api_key=API_KEY)


def test_tidy_search_one(yob):
    searches = [search for search in yob.search("harry potter", max_pages_retrieved=2)]
    tidied = parse_search(searches[0])  # type: ignore
    assert isinstance(tidied, Searches)


def test_tidy_search_multiple(yob):
    searches = [search for search in yob.search("harry potter", max_pages_retrieved=2)]
    tidied = parse_searches(searches)  # type: ignore
    assert isinstance(tidied, Searches)


def test_tidy_video_one(yob):
    videos = [
        video for video in yob.get_video_metadata(ids=["qFagsLxu2Xs", "4MQyV7Wluhs"])
    ]
    tidied = parse_video(videos[0])  # type: ignore
    assert isinstance(tidied, Videos)


def test_tidy_video_multiple(yob):
    videos = [
        video for video in yob.get_video_metadata(ids=["qFagsLxu2Xs", "4MQyV7Wluhs"])
    ]
    tidied = parse_videos(videos)  # type: ignore
    tidied.to_json("test_tidy.json", pretty=True)
    tidied.to_csv("test_tidy.csv")
    assert isinstance(tidied, Videos)


def test_tidy_channel_one(yob):
    ids = ["UC_NN7u1HKTQR6vurmS9iQ1A", "UCMhRG26kBpMp3GAZv5Iv7sw"]
    channels = [ch for ch in yob.get_channel_metadata(ids=ids)]
    tidied = parse_channel(channels[0])  # type: ignore
    assert isinstance(tidied, Channels)


def test_tidy_channel_multiple(yob):
    ids = ["UC_NN7u1HKTQR6vurmS9iQ1A", "UCMhRG26kBpMp3GAZv5Iv7sw"]
    channels = [ch for ch in yob.get_channel_metadata(ids=ids)]
    tidied = parse_channels(channels)  # type: ignore
    assert isinstance(tidied, Channels)


def test_tidy_comment_one(yob):
    cmt_ids = ["Ugxk_z1g6ZmYZ9-ldXF4AaABAg", "UgyXx-EYT7oYvqwp_bJ4AaABAg"]
    comments = [cmt for cmt in yob.get_comment_threads(comment_ids=cmt_ids)]
    with open("hello.json", "w") as f:
        f.write(json.dumps(comments, indent=4, default=str))
    tidied = parse_comment(comments[0])  # type: ignore
    assert isinstance(tidied, Comments)


def test_tidy_comment_multiple(yob):
    cmt_ids = ["Ugxk_z1g6ZmYZ9-ldXF4AaABAg", "UgyXx-EYT7oYvqwp_bJ4AaABAg"]
    comments = [cmt for cmt in yob.get_comment_threads(comment_ids=cmt_ids)]
    tidied = parse_comments(comments)  # type: ignore
    assert isinstance(tidied, Comments)
