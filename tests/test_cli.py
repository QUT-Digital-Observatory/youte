from __future__ import annotations

import csv
import json
import os
from pathlib import Path
from typing import Callable

import pytest
from click.testing import CliRunner

from youte.cli import youte
from youte.collector import Youte
from youte.config import YouteConfig

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
def outfile_json() -> str:
    return "test.json"


@pytest.fixture()
def outfile_jsonl() -> str:
    return "test.jsonl"


@pytest.fixture()
def outfile_csv() -> str:
    return "test.csv"


def _check_csv(csvfile: str | Path) -> bool:
    with open(csvfile, "r", encoding="utf-8-sig") as file:
        f = csv.reader(file)

        headers = next(f)
        rows = list(f)

        assert "id" in headers
        assert len(rows) >= 1

        return True


@pytest.fixture()
def search_params(outfile_json, outfile_jsonl, outfile_csv) -> dict:
    query = "harry potter"
    limit = 2

    params = {
        "standard": [
            "search",
            query,
            "--key",
            API_KEY,
            "--outfile",
            outfile_json,
            "--max-pages",
            limit,
        ],
        "filter-by-language": [
            "search",
            query,
            "-o",
            outfile_json,
            "--lang",
            "vi",
            "--key",
            API_KEY,
            "--max-pages",
            limit,
        ],
        "filter-by-location": [
            "search",
            "harry potter",
            "-o",
            outfile_json,
            "--from",
            "2021-01-01",
            "--to",
            "2021-01-02",
            "--location",
            (27.4705, 153.0260),
            "--radius",
            "500km",
            "--key",
            API_KEY,
            "--limit",
            limit,
        ],
        "tidy-to-csv": [
            "search",
            query,
            "--key",
            API_KEY,
            "--outfile",
            outfile_json,
            "--tidy-to",
            outfile_csv,
            "--max-pages",
            limit,
        ],
        "wrong-order-option": [
            "search",
            query,
            "--from",
            "2021-01-01",
            "--order",
            "alphabet",
            "--key",
            API_KEY,
        ],
        "wrong-date-format": [
            "search",
            query,
            "--outfile",
            outfile_json,
            "--from",
            "10-01-2021",
            "--to",
            "2021-02-01",
            "--key",
            API_KEY,
        ],
    }

    return params


@pytest.mark.parametrize("command", ["wrong-date-format", "wrong-order-option"])
def test_cli_search_fail(runner, search_params, command):
    results = runner.invoke(youte, search_params[command])  # type: ignore
    assert results.exception


def test_cli_search_standard(
    runner,
    tmp_path,
    search_params,
    outfile_json,
    outfile_csv,
):
    with runner.isolated_filesystem(temp_dir=tmp_path) as td:
        runner.invoke(youte, search_params["standard"])  # type: ignore

        with open(outfile_json, "r") as file:
            r: list[dict] = json.loads(file.read())
            assert len(r) > 1
            assert len(r[0]["items"]) > 10
            assert r[0]["_youte"]

        runner.invoke(
            youte,
            ["parse", outfile_json, "--output", outfile_csv],
        )
        assert os.path.exists(outfile_csv)
        assert _check_csv(outfile_csv)


@pytest.mark.parametrize("command", ["filter-by-language", "filter-by-location"])
def test_cli_search_filter(runner, tmp_path, search_params, command, outfile_json):
    with runner.isolated_filesystem(temp_dir=tmp_path) as td:
        runner.invoke(youte, search_params["standard"])  # type: ignore

        with open(outfile_json, "r") as file:
            r: list[dict] = json.loads(file.read())
            assert len(r) > 1
            assert len(r[0]["items"]) > 10
            assert r[0]["_youte"]


def test_cli_search_tidy_csv(runner, tmp_path, search_params, outfile_csv):
    with runner.isolated_filesystem(temp_dir=tmp_path) as td:
        runner.invoke(youte, search_params["tidy-to-csv"])  # type: ignore
        assert os.path.exists(outfile_csv)

        with open(outfile_csv, newline="") as f:
            reader = csv.reader(f)
            rows = [row for row in reader]
        assert len(rows) > 10


# TEST videos COMMAND


@pytest.fixture()
def videos_args(outfile_json) -> list:
    return ["videos", "--key", API_KEY, "-o", outfile_json]


@pytest.mark.parametrize(
    "extra_args",
    [
        ["FZCWXlJWueM"],
        ["FZCWXlJWueM", "9nvdawlwATQ", "XH9-Dx_RwDw"],
        ["--file-path", Path("tests") / "video_ids.csv"],
    ],
    ids=["one_id", "multi_ids", "from_file"],
)
def test_cli_videos(
    runner, tmp_path, videos_args, extra_args, outfile_json, outfile_csv
):
    results = runner.invoke(youte, videos_args + extra_args)  # type: ignore
    assert results.exit_code == 0

    with open(outfile_json, "r") as file:
        r: list[dict] = json.loads(file.read())
        assert len(r[0]["items"]) >= 1
        assert r[0]["_youte"]

    runner.invoke(
        youte,
        ["parse", outfile_json, "--output", outfile_csv],
    )

    assert os.path.exists(outfile_csv)
    assert _check_csv(outfile_csv)

    os.remove(outfile_json)
    os.remove(outfile_csv)


# TEST channels COMMAND


def test_cli_channels(runner, outfile_json, outfile_csv):
    results = runner.invoke(
        youte,
        [
            "channels",
            "-f",
            Path("tests") / "channel_ids.csv",
            "-o",
            outfile_json,
            "--key",
            API_KEY,
        ],
    )
    assert results.exit_code == 0

    with open(outfile_json, "r") as file:
        r: list[dict] = json.loads(file.read())
        assert len(r[0]["items"]) >= 10
        assert r[0]["_youte"]

    runner.invoke(
        youte,
        ["parse", outfile_json, "--output", outfile_csv],
    )
    assert os.path.exists(outfile_csv)
    assert _check_csv(outfile_csv)

    os.remove(outfile_json)


def test_cli_channels_handle(runner, outfile_json, outfile_csv):
    results = runner.invoke(
        youte,
        [
            "channels",
            "--handles",
            "@NextNewsNetwork",
            "-o",
            outfile_json,
            "--key",
            API_KEY,
        ],
    )
    assert results.exit_code == 0

    with open(outfile_json, "r") as file:
        r: list[dict] = json.loads(file.read())
        assert len(r) == 1
        for i in r:
            assert i["items"]
        assert r[0]["_youte"]

    runner.invoke(
        youte,
        ["parse", outfile_json, "--output", outfile_csv],
    )
    assert os.path.exists(outfile_csv)
    assert _check_csv(outfile_csv)

    os.remove(outfile_json)


def test_cli_channels_handles(runner, outfile_json, outfile_csv):
    results = runner.invoke(
        youte,
        [
            "channels",
            "--handles",
            "@NextNewsNetwork,@TurningPointUSA,@BlazeTV,@msnbc,@CNN,@Vox",
            "-o",
            outfile_json,
            "--key",
            API_KEY,
        ],
    )
    assert results.exit_code == 0

    with open(outfile_json, "r") as file:
        r: list[dict] = json.loads(file.read())
        assert len(r) == 6
        for i in r:
            assert i["items"]
        assert r[0]["_youte"]

    runner.invoke(
        youte,
        ["parse", outfile_json, "--output", outfile_csv],
    )
    assert os.path.exists(outfile_csv)
    assert _check_csv(outfile_csv)

    os.remove(outfile_json)


def test_cli_channels_both(runner, outfile_json, outfile_csv):
    results = runner.invoke(
        youte,
        [
            "channels",
            "-f",
            Path("tests") / "channel_ids.csv",
            "--handles",
            "@NextNewsNetwork,@TurningPointUSA,@BlazeTV,@msnbc,@CNN,@Vox",
            "-o",
            outfile_json,
            "--key",
            API_KEY,
        ],
    )
    assert results.exit_code == 0

    with open(outfile_json, "r") as file:
        r: list[dict] = json.loads(file.read())
        assert len(r) > 6
        for i in r:
            assert i["items"]
        assert r[0]["_youte"]

    runner.invoke(
        youte,
        ["parse", outfile_json, "--output", outfile_csv],
    )
    assert os.path.exists(outfile_csv)
    assert _check_csv(outfile_csv)

    os.remove(outfile_json)


# TEST comments COMMAND


@pytest.fixture()
def comment_args(outfile_json) -> list:
    return ["comments", "--key", API_KEY, "-o", outfile_json]


@pytest.mark.parametrize(
    "extra_args",
    [
        ["-v", "XmYnsO7iSI8"],
        ["-v", "XmYnsO7iSI8", "4oqjcKenCH8", "_b6NgY_pMdw"],
        ["-v", "--file-path", Path("tests") / "ids_to_get_comment.csv"],
    ],
    ids=["one_id", "multi_ids", "from_file"],
)
def test_cli_comments(runner, comment_args, extra_args, outfile_json, outfile_csv):
    results = runner.invoke(youte, comment_args + extra_args)
    assert results.exit_code == 0

    with open(outfile_json, "r") as file:
        r: list[dict] = json.loads(file.read())
        assert len(r[0]["items"]) >= 10
        assert r[0]["_youte"]

    runner.invoke(
        youte,
        ["parse", outfile_json, "--output", outfile_csv],
    )

    assert os.path.exists(outfile_csv)
    assert _check_csv(outfile_csv)

    os.remove(outfile_json)


# TEST dehydrate COMMAND


def test_cli_dehydrate(runner):
    results = runner.invoke(youte, ["dehydrate", "tests/search_results.jsonl"])  # type: ignore
    assert results.exit_code == 0
    assert "AYdQvnWtEHU" in results.output


@pytest.mark.parametrize("country", ["au", "vn"])
def test_cli_chart(runner, country, outfile_json, outfile_csv):
    results = runner.invoke(
        youte,  # type: ignore
        ["chart", country, "--outfile", outfile_json, "--key", API_KEY],
    )
    assert results.exit_code == 0

    with open(outfile_json, "r") as file:
        r: list[dict] = json.loads(file.read())
        assert len(r[0]["items"]) >= 10
        assert r[0]["_youte"]

    runner.invoke(
        youte,
        ["parse", outfile_json, "--output", outfile_csv],
    )

    assert os.path.exists(outfile_csv)
    assert _check_csv(outfile_csv)

    os.remove(outfile_json)
