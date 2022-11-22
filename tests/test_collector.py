import os
import json
import pytest
from click.testing import CliRunner

from youte.config import YouteConfig
from youte.collector import Youte
from youte.__main__ import youte


API_KEY = os.environ["STAGING_API_KEY"]
NAME = "tester"


@pytest.fixture()
def config_path(tmp_path):
    config_name = "test_config"
    return tmp_path / config_name


def test_config_empty(config_path):
    youte_conf = YouteConfig(filename=str(config_path))
    assert not config_path.exists()


def test_config_add(config_path):
    youte_conf = YouteConfig(filename=str(config_path))
    youte_conf.add_profile(NAME, API_KEY)

    assert config_path.exists()


@pytest.fixture()
def youte_obj(config_path) -> Youte:
    youte_obj = Youte(api_key=API_KEY)
    yield youte_obj
    if os.path.exists(".youte.history"):
        os.rmdir(".youte.history")


@pytest.fixture()
def runner() -> CliRunner:
    runner = CliRunner()
    yield runner
    try:
        os.remove("youte.log")
    except FileNotFoundError:
        pass


def test_empty_youte(youte_obj):
    assert youte_obj.api_key == API_KEY


def test_search(youte_obj):
    params = {
        "part": "snippet",
        "maxResults": 50,
        "type": "video",
        "order": "relevance",
        "publishedAfter": "2022-10-01",
    }
    search = youte_obj.search(query="harry potter", **params)
    page = 0
    total_responses = 0

    for results in search:
        if page >= 3:
            break
        total_responses += len(results["items"])
        page += 1

    assert 50 < total_responses < 200
    assert youte_obj.history_file.exists()


@pytest.fixture()
def search_params() -> dict:
    params = {
        "standard-no-output": [
            "search",
            "harry potter",
            "--from",
            "2021-01-01",
            "--to",
            "2021-02-01",
            "--key",
            API_KEY,
        ],
        "standard-output": [
            "search",
            "harry potter",
            "--from",
            "2021-01-01",
            "--to",
            "2021-02-01",
            "--key",
            API_KEY,
            "output.json",
        ],
        "wrong-date-format": [
            "search",
            "harry potter",
            "--from",
            "10-01-2021",
            "--to",
            "2021-02-01",
            "--key",
            API_KEY,
        ],
        "ordered-by-relevance": [
            "search",
            "harry potter",
            "--from",
            "2021-01-01",
            "--order",
            "relevance",
            "--key",
            API_KEY,
        ],
        "wrong-order-option": [
            "search",
            "harry potter",
            "--from",
            "2021-01-01",
            "--order",
            "alphabet",
            "--key",
            API_KEY,
        ],
        "safe-search": [
            "search",
            "harry potter",
            "--from",
            "2021-01-01",
            "--safe-search",
            "moderate",
            "--key",
            API_KEY,
        ],
        "long-videos": [
            "search",
            "harry potter",
            "--from",
            "2021-01-01",
            "--safe-search",
            "moderate",
            "--video-duration",
            "long",
            "--key",
            API_KEY,
        ],
        "no-query": ["search", "--from", "2022-08-01", "--key", API_KEY],
    }

    return params


@pytest.mark.parametrize(
    "command", ["wrong-date-format", "wrong-order-option", "no-query"]
)
def test_cli_search_fail(runner, search_params, command):
    results = runner.invoke(youte, search_params[command])
    assert results.exception


@pytest.mark.parametrize(
    "command",
    ["standard-no-output", "ordered-by-relevance", "safe-search", "long-videos"],
)
def test_cli_search(runner, search_params, command):
    results = runner.invoke(youte, search_params[command])
    assert results.exit_code == 0
    assert "youtube#searchListResponse" in results.output


def test_cli_search_output(runner, tmp_path, search_params):
    with runner.isolated_filesystem(temp_dir=tmp_path) as td:
        runner.invoke(youte, search_params["standard-output"])
        assert os.path.exists("output.json")

        with open("output.json", "r") as file:
            row = file.readline()
            r = json.loads(row)

            assert len(r["items"]) > 10
