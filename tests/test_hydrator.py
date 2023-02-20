import os
import pytest
from click.testing import CliRunner
from pathlib import Path

from youte.cli import youte

API_KEY = os.environ["STAGING_API_KEY"]
NAME = "tester"


@pytest.fixture()
def runner() -> CliRunner:
    runner = CliRunner()
    yield runner
    try:
        os.remove("youte.log")
    except FileNotFoundError:
        pass


def test_hydrate_no_input(runner):
    results = runner.invoke(youte, ["hydrate"])
    assert results.exception


@pytest.fixture()
def hydrate_args() -> list:
    return ["hydrate", "--key", API_KEY]


@pytest.mark.parametrize(
    "extra_args",
    [
        ["FZCWXlJWueM"],
        ["FZCWXlJWueM", "9nvdawlwATQ", "XH9-Dx_RwDw"],
        ["--file-path", Path("tests") / "video_ids.csv"],
    ],
    ids=["one_id", "multi_ids", "from_file"],
)
def test_hydrate_video(runner, hydrate_args, extra_args):
    results = runner.invoke(youte, hydrate_args + extra_args)
    assert results.exit_code == 0
    assert "youtube#videoListResponse" in results.output
    assert "title" in results.output


def test_hydrate_channel(runner, hydrate_args):
    results = runner.invoke(
        youte,
        hydrate_args + ["-f", Path("tests") / "channel_ids.csv", "--kind=channels"],
    )
    assert results.exit_code == 0
    assert "youtube#channelListResponse" in results.output
    assert "title" in results.output


@pytest.fixture()
def comment_args() -> list:
    return ["get-comments", "--key", API_KEY]


@pytest.mark.parametrize(
    "extra_args",
    [
        ["-v", "XmYnsO7iSI8"],
        ["-v", "XmYnsO7iSI8", "4oqjcKenCH8", "_b6NgY_pMdw"],
        ["-v", "--file-path", Path("tests") / "ids_to_get_comment.csv"],
    ],
    ids=["one_id", "multi_ids", "from_file"],
)
def test_get_comments_on_video(runner, comment_args, extra_args):
    results = runner.invoke(youte, comment_args + extra_args)
    assert results.exit_code == 0
    assert "youtube#commentThreadListResponse" in results.output
    assert "topLevelComment" in results.output


def test_dehydrate(runner):
    results = runner.invoke(youte, ["dehydrate", "tests/search_results.json"])
    assert results.exit_code == 0
    assert "AYdQvnWtEHU" in results.output


def test_dehydrate_fail(runner):
    results = runner.invoke(youte, ["dehydrate", "tests/channel_ids.csv"])
    assert results.exception
