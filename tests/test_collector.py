import os
import json
import pytest
from click.testing import CliRunner
from pathlib import Path

from youte.config import YouteConfig
from youte.collector import Youte
from youte.cli import youte


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


@pytest.fixture()
def search_params() -> dict:
    params = {
        "standard-no-output": [
            "search",
            "harry potter",
            "--from",
            "2021-01-01",
            "--key",
            API_KEY,
            "--limit",
            "2"
        ],
        "standard-output": [
            "search",
            "harry potter",
            "--from",
            "2021-01-01",
            "--to",
            "2021-01-02",
            "--key",
            API_KEY,
            "--output",
            "output.json",
            "--limit",
            "2"
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
            "--limit",
            "2"
        ],
        "ordered-by-relevance": [
            "search",
            "harry potter",
            "--order",
            "relevance",
            "--key",
            API_KEY,
            "--limit",
            "2"
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
            "--limit",
            "2"
        ],
        "safe-search": [
            "search",
            "harry potter",
            "--from",
            "2021-01-01",
            "--to",
            "2021-01-02",
            "--safe-search",
            "moderate",
            "--key",
            API_KEY,
            "--limit",
            "2"
        ],
        "long-videos": [
            "search",
            "harry potter",
            "--from",
            "2021-01-01",
            "--to",
            "2021-01-02",
            "--safe-search",
            "moderate",
            "--video-duration",
            "long",
            "--key",
            API_KEY,
            "--limit",
            "2"
        ],
        "no-query": ["search", "--from", "2022-08-01", "--key", API_KEY],
    }

    return params


@pytest.mark.parametrize(
    "command", ["wrong-date-format", "wrong-order-option"]
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

            assert len(r["items"]) > 5


@pytest.fixture()
def related_params() -> dict:
    return {
        "one-id": [
            "get-related",
            "f3m_WqxhL4o",
            "--output",
            "related.json"
        ],
        "multi-ids": [
            "get-related",
            "f3m_WqxhL4o",
            "17yO5AssjAI",
            "--output",
            "related.json"
        ],
        "from-file": [
            "get-related",
            "-f",
            (Path("tests") / "related_ids.csv").resolve(),
            "--output",
            "related.json"
        ]
    }


@pytest.mark.parametrize(
    "command",
    ["one-id", "multi-ids", "from-file"]
)
def test_cli_related_search(runner, tmp_path, related_params, command):
    with runner.isolated_filesystem(temp_dir=tmp_path) as td:
        runner.invoke(youte, related_params[command])
        assert os.path.exists("related.json")

        with open("related.json", "r") as file:
            row = file.readline()
            r = json.loads(row)

            assert len(r["items"]) > 10


@pytest.mark.parametrize(
    "country",
    [None, "au", "vn"]
)
def test_cli_most_popular(runner, tmp_path, country):
    with runner.isolated_filesystem(temp_dir=tmp_path) as td:
        runner.invoke(youte, ["most-popular", "test.json", "-r", country])
        assert os.path.exists("test.json")

        with open("test.json", "r") as file:
            row = file.readline()
            r = json.loads(row)

            assert len(r["items"]) > 40
