"""
Copyright: Digital Observatory 2022 <digitalobservatory@qut.edu.au>
Author: Boyd Nguyen <thaihoang.nguyen@qut.edu.au>
"""
import json
import logging
import os
import sys
from json.decoder import JSONDecodeError
from pathlib import Path
from typing import List, Sequence

import click

from youte import tidier
from youte.collector import Youte, _get_history_path
from youte.config import YouteConfig, get_api_key, get_config_path
from youte.exceptions import StopCollector
from youte.utilities import validate_date_string

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


def _validate_date(ctx, param, value):
    if value:
        if validate_date_string(value):
            return value
        else:
            raise click.BadParameter("Date not in correct format (YYYY-MM-DD)")


# CLI argument set up:
@click.group()
@click.version_option()
def youte():
    """
    Utility to collect and tidy YouTube meta-data and comments via YouTube API.
    Run `youte --help` to get started.
    """
    pass


@youte.command()
@click.argument("query", required=True)
@click.argument("output", type=click.File(mode="w"), required=False)
@click.option(
    "--from", "from_", help="Start date (YYYY-MM-DD)", callback=_validate_date
)
@click.option("--to", help="End date (YYYY-MM-DD)", callback=_validate_date)
@click.option(
    "--type",
    "type_",
    default="video",
    help="Type of resource to search for",
    show_default=True,
)
@click.option("--name", help="Specify an API key name added to youte config")
@click.option("--key", help="Specify a YouTube API key")
@click.option(
    "--order",
    type=click.Choice(
        ["date", "rating", "relevance", "title", "videoCount", "viewCount"],
        case_sensitive=False,
    ),
    help="Sort results",
    show_default=True,
    default="date",
)
@click.option(
    "--safe-search",
    type=click.Choice(["none", "moderate", "strict"], case_sensitive=False),
    help="Include or exclude restricted content",
    default="none",
    show_default=True,
)
@click.option(
    "--video-duration",
    type=click.Choice(["any", "long", "medium", "short"]),
    help="Include videos of a certain duration",
)
@click.option(
    "--channel-type",
    type=click.Choice(["any", "show"]),
    help="Restrict search to a particular type of channel",
)
@click.option(
    "--video-type",
    type=click.Choice(["any", "episode", "movie"]),
    help="Search a particular type of videos",
)
@click.option(
    "--caption",
    type=click.Choice(["any", "closedCaption", "none"]),
    help="Filter videos based on if they have captions",
)
@click.option(
    "--definition",
    "--video-definition",
    "video_definition",
    type=click.Choice(["any", "high", "standard"]),
    help="Include videos by definition",
)
@click.option(
    "--dimension",
    "--video-dimension",
    "video_dimension",
    type=click.Choice(["any", "2d", "3d"]),
    help="Search 2D or 3D videos",
)
@click.option(
    "--embeddable",
    "--video-embeddable",
    "video_embeddable",
    type=click.Choice(["any", "true"]),
    help="Search only embeddable videos",
)
@click.option(
    "--license",
    "--video-license",
    "video_license",
    type=click.Choice(["any", "creativeCommon", "youtube"]),
    help="Include videos with a certain license",
)
@click.option(
    "--max-results",
    type=click.IntRange(0, 50),
    help="Maximum number of results returned per page",
    default=50,
    show_default=True,
)
@click.option("--resume", help="Resume progress from this file")
@click.option("--to-csv", type=click.Path(), help="Tidy data to CSV file")
def search(
    query: str,
    output: str,
    from_: str,
    to: str,
    name: str,
    key: str,
    order: str,
    video_duration: str,
    type_: str,
    channel_type: str,
    video_type: str,
    caption: str,
    video_definition: str,
    video_dimension: str,
    video_embeddable: str,
    video_license: str,
    safe_search: str,
    resume: str,
    to_csv: str,
    max_results: int,
) -> None:
    """Do a YouTube search.

    QUERY: search query

    OUTPUT: name of json file to store output data
    """
    api_key = key if key else get_api_key(name=name)
    search_collector = _set_up_collector(api_key=api_key)

    params = {
        "part": "snippet",
        "maxResults": max_results,
        "order": order,
        "safeSearch": safe_search,
        "videoDuration": video_duration,
        "type": type_,
        "channelType": channel_type,
        "videoCaption": caption,
        "videoDefinition": video_definition,
        "videoDimension": video_dimension,
        "videoEmbeddable": video_embeddable,
        "videoLicense": video_license,
        "videoType": video_type,
    }

    if from_:
        params["publishedAfter"] = from_
    if to:
        params["publishedBefore"] = to

    try:
        if resume:
            if not _get_history_path(resume).exists():
                raise click.BadParameter("No such history file found")

        results = search_collector.search(
            query=query, save_progress_to=resume, **params
        )

        click.echo(params)

        for result in results:
            click.echo(json.dumps(result), file=output)

            if to_csv:
                items = result["items"]
                tidier.tidy_to_csv(items=items, output=to_csv, resource_kind="search")

        if output:
            click.echo(f"Results are stored in {output.name}")

    except StopCollector:
        _prompt_save_progress(search_collector.history_file)


@youte.command()
@click.argument("items", nargs=-1, required=False)
@click.option("-o", "--output", type=click.File(mode="w"), required=False)
@click.option("-f", "--file-path", help="Get IDs from file", default=None)
@click.option(
    "-t",
    "--by-thread",
    "by_parent",
    help="Get all replies to a parent comment",
    is_flag=True,
)
@click.option("-v", "--by-video", help="Get all comments for a video ID", is_flag=True)
@click.option("--name", help="Specify an API key name added to youte config")
@click.option("--key", help="Specify a YouTube API key")
@click.option("--to-csv", type=click.Path(), help="Tidy data to CSV file")
def get_comments(
    items: Sequence[str],
    output: str,
    name: str,
    key: str,
    file_path: str,
    by_video: bool,
    by_parent: bool,
    to_csv,
) -> None:
    """
    Get YouTube comments by video IDs or thread IDs.

    The IDs should all belong to one type, i.e. either video or comment thread.
    You cannot mix both video AND comment thread IDs in one command.

    OUTPUT: name of JSON file to store output

    ITEMS: ID(s) of item as provided by YouTube
    """
    api_key = key if key else get_api_key(name=name)
    collector = _set_up_collector(api_key=api_key)

    ids = _get_ids(string=items, file=file_path)

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

    results = collector.list_items(item_type=item_type, ids=ids, by=by)

    for result in results:
        click.echo(json.dumps(result), file=output)

        if to_csv:
            items = result["items"]
            tidier.tidy_to_csv(items=items, output=to_csv, resource_kind="comments")

    if output:
        click.echo(f"Results are stored in {output.name}")


@youte.command()
@click.argument("items", nargs=-1, required=False)
@click.option("-o", "--output", type=click.File(mode="w"), required=False)
@click.option("-f", "--file-path", help="Get IDs from file", default=None)
@click.option(
    "--kind",
    type=click.Choice(["videos", "channels", "comments"], case_sensitive=False),
    help="Sort results",
    show_default=True,
    default="videos",
)
@click.option("--name", help="Specify an API key name added to youte config")
@click.option("--key", help="Specify a YouTube API key")
@click.option("--to-csv", type=click.Path(), help="Tidy data to CSV file")
def hydrate(
    items: Sequence[str],
    output: str,
    kind: str,
    file_path: str,
    name: str,
    key: str,
    to_csv,
) -> None:
    """Hydrate YouTube resource IDs.

    Get all metadata for a list of resource IDs.
    By default, the function hydrates video IDs.

    The IDs should all belong to one type, i.e. either video, channel, or comment.
    For example, you cannot mix both video AND channel IDs in one command.

    OUTPUT: name of JSON file to store output

    ITEMS: ID(s) of item as provided by YouTube
    """
    api_key = key if key else get_api_key(name=name)
    collector = _set_up_collector(api_key=api_key)

    ids = _get_ids(string=items, file=file_path)

    results = collector.list_items(item_type=kind, ids=ids)

    for result in results:
        click.echo(json.dumps(result), file=output)

        if to_csv:
            items = result["items"]
            tidier.tidy_to_csv(items=items, output=to_csv, resource_kind=kind)

    if output:
        click.echo(f"Results are stored in {output.name}")


@youte.command()
@click.argument("infile", type=click.Path())
@click.option(
    "-o", "--output", type=click.File(mode="w"), help="Output text file to store IDs in"
)
def dehydrate(infile, output: str) -> None:
    """Extract an ID list from a file of YouTube resources

    INFILE: JSON file of YouTube resources
    """
    try:
        items = tidier.get_items(infile)
        ids = tidier.get_id(items)
        for id_ in ids:
            click.echo(id_, file=output)
    except JSONDecodeError:
        raise click.BadParameter("File is not JSON.")


@youte.command()
@click.argument("filepath", type=click.Path(), required=True)
@click.argument("output", type=click.Path(), required=True)
def tidy(filepath, output):
    """Tidy raw JSON response into relational SQLite databases"""
    tidier.master_tidy(filepath=filepath, output=output)


@youte.command()
def list_history():
    """List resumable history files"""
    if not os.path.exists(".youte.history"):
        click.echo("No history file found")

    files = os.listdir(".youte.history")
    if not files:
        click.echo("No history file found")
    else:
        for file in files:
            click.echo(file.removesuffix(".db"))


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
    click.echo("To get started, an API key is required to get data from Youtube API.")
    click.echo()
    click.echo("To obtain an API key, follow the steps in")
    click.echo("https://developers.google.com/youtube/v3/getting-started")
    click.echo()
    click.echo("Once you have an API key, run `youte configure add-key` to start.")

    click.secho("Setting up you Youtube configuration...", fg="magenta")
    click.echo()
    api_key = click.prompt("Enter your API key")
    username = click.prompt("What would you name this key?")

    config_file_path = Path(get_config_path())

    if not config_file_path.parent.exists():
        click.echo()
        click.secho(
            "Creating config folder at %s" % config_file_path.parent, fg="magenta"
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
    click.echo("To set a default key, run `youte config set-default <name-of-key>`")


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
            bold=True,
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
                click.secho("%s -------- %s (*)" % (name, conf[name]["key"]), fg="blue")
            else:
                click.echo("%s -------- %s" % (name, conf[name]["key"]))
        click.echo()
        click.secho(
            "All API keys are stored in %s" % get_config_path(), fg="green", bold=True
        )
        click.echo()


def _set_up_collector(api_key: str) -> Youte:
    collector = Youte(api_key=api_key)

    return collector


def _set_up_config(filename=get_config_path()) -> YouteConfig:
    config_file = YouteConfig(filename=filename)

    return config_file


def _get_ids(string: Sequence[str] = None, file: str = None) -> List[str]:
    _raise_no_item_error(items=string, file_path=file)

    if string:
        ids = list(string)

    if file:
        with open(file, mode="r") as f:
            ids = [row.rstrip() for row in f.readlines()]

    return ids


def _raise_no_item_error(items: Sequence[str], file_path: str) -> None:
    if not (items or file_path):
        click.secho(
            "No item ID is specified. Pass some item IDs or specify " "a file.",
            fg="red",
            bold=True,
        )
        sys.exit(1)


def _prompt_save_progress(filename) -> None:
    if click.confirm("Do you want to save your current progress?"):
        full_path = Path(filename).resolve()
        click.echo(f"Progress saved at {full_path}")
        click.echo(
            f"To resume progress, run the same youte search command "
            f"and add `--resume {full_path.stem}`"
        )
    else:
        try:
            os.remove(filename)
        except FileNotFoundError:
            pass
    sys.exit(0)
