import os
import pytest
from click.testing import CliRunner

from youte.cli import youte


@pytest.fixture()
def runner() -> CliRunner:
    runner = CliRunner()
    yield runner
    try:
        os.remove("youte.log")
    except FileNotFoundError:
        pass


@pytest.mark.parametrize(
    "file",
    [
        "tests/search_results.json",
        "tests/videos.json",
        "tests/channels.json",
        "tests/comments.json",
    ],
    ids=["search", "videos", "channels", "comments"],
)
def test_tidy(runner, tmp_path, file):
    results = runner.invoke(youte, ["tidy", file, str(tmp_path / "output.db")])
    assert results.exit_code == 0
    assert (tmp_path / "output.db").exists()
