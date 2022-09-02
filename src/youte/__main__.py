"""
Copyright: Digital Observatory 2022 <digitalobservatory@qut.edu.au>
Author: Boyd Nguyen <thaihoang.nguyen@qut.edu.au>
"""
import logging
import sys

import click
from pathlib import Path

from youte.collector import Youte
from youte.config import YouteConfig, get_api_key, get_config_path
from youte.quota import Quota
from youte import tidier

# Logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler("youte.log")
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter(
    "%(asctime)s - %(module)s: %(message)s (%(levelname)s)"
)
file_handler.setFormatter(file_formatter)

logger.addHandler(file_handler)


# CLI argument set up:
@click.group()
def youte():
    """
    Utility to collect and tidy YouTube meta-data and comments via YouTube API.
    Run `youte config --help` to get started.
    """
    pass


@youte.command()
@click.argument("query", required=True)
@click.argument("output", required=True)
@click.option("--from", "from_", help="Start date (YYYY-MM-DD)")
@click.option("--to", help="End date (YYYY-MM-DD)")
@click.option("--name", help="Name of the API key (optional)")
@click.option("--order",
              type=click.Choice(['date', 'rating', 'relevance', 'title'],
                                case_sensitive=False),
              help="Sort results",
              show_default=True,
              default='date')
@click.option("--safe-search",
              type=click.Choice(['none', 'moderate', 'strict'],
                                case_sensitive=False),
              help="Include or exclude restricted content",
              default='none',
              show_default=True)
@click.option(
    "--max-quota", default=10000, help="Maximum quota allowed",
    show_default=True
)
def search(
        query: str,
        output: str,
        from_: str,
        to: str,
        name: str,
        max_quota: int,
        order: str,
        safe_search: str
        # get_id=False,
) -> None:
    """Do a YouTube search."""

    api_key = get_api_key(name=name)

    search_collector = _set_up_collector(api_key=api_key, max_quota=max_quota)

    meta_data = "kind,etag,nextPageToken,regionCode,pageInfo"
    # fields = f"{meta_data},items/id/videoId" if get_id else "*"

    params = {
        "part": "snippet",
        "maxResults": 50,
        "type": "video",
        "order": order,
        "safeSearch": safe_search
    }

    if from_:
        params["publishedAfter"] = from_
    if to:
        params["publishedBefore"] = to

    search_collector.search(query=query, output_path=output, **params)


@youte.command()
@click.argument("filepath", required=True)
@click.argument("output", required=True)
@click.option(
    "-p", "--by-parent", help="Get all replies to a parent comment",
    is_flag=True
)
@click.option("-v", "--by-video", help="Get all comments for a video ID",
              is_flag=True)
@click.option(
    "--max-quota", default=10000, help="Maximum quota allowed",
    show_default=True
)
@click.option("--name", help="Name of the API key (optional)")
def list_comments(
        filepath: str, output: str, max_quota: int, name: str, by_video,
        by_parent
) -> None:
    """
    Get YouTube comments from a list of comment/channel/video ids.

    By default, get all comments from a list of comment ids.
    """

    api_key = get_api_key(name=name)

    collector = _set_up_collector(api_key=api_key, max_quota=max_quota)

    with open(filepath, mode="r") as filepath:
        ids = [row.rstrip() for row in filepath.readlines()]

    if by_video and by_parent:
        click.secho(
            "Both video and parent flags are on. Only one is allowed.",
            fg="red",
            bold=True,
        )
        sys.exit(1)

    item_type = "comments" if by_parent else "comment_threads"

    if by_video:
        by = "video"
    elif by_parent:
        by = "parent"
    else:
        by = None

    collector.list_items(item_type=item_type, ids=ids, output_path=output,
                         by=by)


@youte.command()
@click.argument("filepath", required=True)
@click.argument("output", required=True)
@click.option(
    "--channel", help="Hydrate channel IDs instead of video IDs", is_flag=True
)
@click.option("--name", help="Name of the API key (optional)")
@click.option(
    "--max-quota", default=10000, help="Maximum quota allowed",
    show_default=True
)
def hydrate(filepath, output, channel, name, max_quota):
    """Hydrate video or channel ids.

    Get all metadata for a list of video or channel IDs.
    By default, the function hydrates video IDs.
    """

    api_key = get_api_key(name=name)

    collector = _set_up_collector(api_key=api_key, max_quota=max_quota)

    with open(filepath, mode="r") as filepath:
        ids = [row.rstrip() for row in filepath.readlines()]

    item_type = "channels" if channel else "videos"
    collector.list_items(item_type=item_type, ids=ids, output_path=output)


@youte.command()
@click.argument("filepath", required=True)
@click.argument("output", required=True)
def tidy(filepath, output):
    """Tidy raw JSON response into relational SQLite databases"""
    tidier.master_tidy(filepath=filepath, output=output)


@youte.group()
def config():
    """
    Set up API keys to access data from YouTube API.
    """


@config.command()
def add_key():
    """
    Add YouTube API key
    """
    click.echo()
    click.secho("Welcome to youte!", fg="green", bold=True)
    click.echo("Configuring your profile...")
    click.echo()
    click.echo(
        "To get started, an API key is required to get data from Youtube API."
    )
    click.echo()
    click.echo("To obtain an API key, follow the steps in")
    click.echo("https://developers.google.com/youtube/v3/getting-started.")
    click.echo()
    click.echo(
        "Once you have an API key, run `youte configure add-key` to start.")

    click.secho("Setting up you Youtube configuration...", fg="magenta")
    click.echo()
    api_key = click.prompt("Enter your API key")
    username = click.prompt("What would you name this key?")

    config_file_path = Path(get_config_path())

    if not config_file_path.parent.exists():
        click.echo()
        click.secho(
            "Creating config folder at %s" % config_file_path.parent,
            fg="magenta"
        )
        config_file_path.parent.mkdir(parents=True)

    conf = _set_up_config()
    click.echo(f"Config file is stored at {config_file_path.resolve()}.")

    conf.add_profile(name=username, key=api_key)
    click.echo()
    if click.confirm("Set this API key as default?"):
        conf.set_default(username)
    click.echo()
    click.secho("API key successfully configured!", fg="green", bold=True)
    click.echo()
    click.echo("To add more API keys, rerun `youte config add-key`.")
    click.echo(
        "To set an API key as default, run `youte config set-default" " <name-of-key>"
    )


@config.command()
@click.argument("name")
def set_default(name):
    """Set default API key"""
    click.echo("Setting %s as default key" % name)
    conf = _set_up_config()
    try:
        conf.set_default(name)
        click.echo("%s is now your default API key" % conf[name]["key"])
    except KeyError:
        click.secho(
            """No such name found.
            You might not have added this profile or
            added it under a different name.
            Run:
            - `youte init list-keys` to see the list of registered keys.
            - `youte init add-key to add a new API key.
            """,
            fg="red",
            bold=True
        )


@config.command()
@click.argument("name")
def remove(name):
    """Delete stored API key"""
    conf = _set_up_config()
    conf.delete_profile(name=name)
    click.echo(f"Profile `{name}` successfully removed!")


@config.command()
def list_keys():
    """Show a list of keys already added"""
    click.echo()
    conf = _set_up_config()

    if not Path(get_config_path()).exists():
        click.echo("No API key has been added to config file.")
    else:
        for name in conf:
            if "default" in conf[name]:
                click.secho(
                    "%s -------- %s (*)" % (name, conf[name]["key"]),
                    fg="blue"
                )
            else:
                click.echo("%s -------- %s" % (name, conf[name]["key"]))
        click.echo()
        click.secho(
            "All API keys are stored in %s" % get_config_path(), fg="green",
            bold=True
        )
        click.echo()


def _set_up_collector(api_key, max_quota):
    quota = Quota(api_key=api_key, config_path=get_config_path())
    collector = Youte(api_key=api_key, max_quota=max_quota)
    collector.quota = quota

    return collector


def _set_up_config(filename=get_config_path()) -> YouteConfig:
    config_file = YouteConfig(filename=filename)

    return config_file
