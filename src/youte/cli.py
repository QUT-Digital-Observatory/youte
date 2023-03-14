"""
Copyright: Digital Observatory 2022 <digitalobservatory@qut.edu.au>
Author: Boyd Nguyen <thaihoang.nguyen@qut.edu.au>
"""
from __future__ import annotations

import logging
import sys
from json.decoder import JSONDecodeError
from pathlib import Path
from typing import IO, Literal

import click

import youte.parser as parser
from youte.collector import Youte
from youte.config import YouteConfig
from youte.exceptions import ValueAlreadyExists
from youte.utilities import export_file, retrieve_ids_from_file, validate_date_string

# Logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter("%(levelname)s: %(message)s")
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)


# file_handler = logging.FileHandler("youte.log")
# file_handler.setLevel(logging.INFO)
# file_formatter = logging.Formatter(
#     "%(asctime)s - %(module)s: %(message)s (%(levelname)s)"
# )
# file_handler.setFormatter(file_formatter)
#
# logger.addHandler(file_handler)


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
@click.argument("query")
@click.option(
    "-o",
    "--outfile",
    type=click.Path(),
    help="Name of json file to store results to",
    required=True,
)
@click.option(
    "--output-format",
    default="json",
    type=click.Choice(["json", "jsonl"]),
    help="Format of the output file",
    show_default=True,
)
@click.option("--pretty", "-p", is_flag=True, help="Pretty print JSON")
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
    "--lang",
    help="Return results most relevant to a language (ISO 639-1 two-letter code)",
)
@click.option(
    "--region",
    default="US",
    help="Return videos viewable in the specified country (ISO 3166-1 alpha-2 code)",
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
    "--location",
    nargs=2,
    type=click.FLOAT,
    help="Lat and long coordinates to restrict search to. --radius must be specified",
)
@click.option(
    "--radius",
    help="Define the geographic area to restrict search. Must be a number with a unit",
)
@click.option(
    "--max-results",
    type=click.IntRange(0, 50),
    help="Maximum number of results returned per page",
    default=50,
    show_default=True,
)
@click.option(
    "--max-pages",
    "-m",
    type=click.INT,
    help="Maximum number of result pages to retrieve",
)
@click.option("--tidy-to", type=click.Path(), help="Parse data and export to file")
@click.option(
    "--format",
    "format_",
    type=click.Choice(["json", "csv"]),
    default="csv",
    help="Format data is parsed into. Can be 'json', 'jsonl', or 'csv'",
    show_default=True,
)
def search(
    query: str,
    outfile: Path,
    output_format: Literal["json", "jsonl"],
    pretty: bool,
    from_: str,
    to: str,
    name: str,
    key: str,
    order: Literal["date", "rating", "relevance", "title", "videoCount", "viewCount"],
    video_duration: Literal["any", "long", "medium", "short"],
    lang: str,
    region: str,
    type_: str,
    channel_type: Literal["any", "show"],
    video_type: Literal["any", "episode", "movie"],
    caption: Literal["any", "closedCaption", "none"],
    video_definition: Literal["any", "high", "standard"],
    video_dimension: Literal["any", "2d", "3d"],
    video_embeddable: Literal["any", "true"],
    video_license: Literal["any", "creativeCommon", "youtube"],
    safe_search: Literal["none", "moderate", "strict"],
    location: tuple[float],
    radius: str,
    tidy_to: Path,
    format_: Literal["json", "jsonl", "csv"],
    max_pages: int,
    max_results: int,
) -> None:
    """Do a YouTube search

    QUERY: search query
    """
    api_key = key if key else _get_api_key(name=name)
    yob = Youte(api_key=api_key)

    results = [
        result
        for result in yob.search(
            query=query,
            type_=type_,
            start_time=from_,
            end_time=to,
            order=order,
            safe_search=safe_search,
            language=lang,
            region=region,
            video_duration=video_duration,
            video_type=video_type,
            caption=caption,
            video_definition=video_definition,
            video_embeddable=video_embeddable,
            location=location,
            location_radius=radius,
            video_dimension=video_dimension,
            max_pages_retrieved=max_pages,
            max_result=max_results,
            video_license=video_license,
            channel_type=channel_type,
        )
    ]

    export_file(
        results, fp=outfile, file_format=output_format, pretty=pretty, ensure_ascii=True
    )

    if tidy_to:
        if format_ == "csv":
            parser.parse_searches(results).to_csv(tidy_to)
        elif format_ == "json":
            parser.parse_searches(results).to_json(tidy_to)


@youte.command()
@click.argument("items", nargs=-1, required=False)
@click.option(
    "-o",
    "--outfile",
    type=click.Path(),
    help="Name of json file to store results to",
)
@click.option(
    "--output-format",
    default="json",
    type=click.Choice(["json", "jsonl"]),
    help="Format of the output file",
    show_default=True,
)
@click.option("--pretty", "-p", is_flag=True, help="Pretty print JSON")
@click.option("-f", "--file-path", help="Use IDs from file", default=None)
@click.option(
    "--order",
    type=click.Choice(["time", "relevance"]),
    default="time",
    show_default=True,
    help="Specify how comment threads are sorted",
)
@click.option(
    "--text-format",
    type=click.Choice(["html", "plainText"]),
    default="html",
    show_default=True,
    help="Specify the text format of the returned data",
)
@click.option(
    "--query", "-q", help="Only retrieve comment threads matching search terms"
)
@click.option(
    "-c",
    "--by-channel-id",
    help="Get comments associated with one or a list channel",
    is_flag=True,
)
@click.option(
    "--max-results",
    type=click.IntRange(0, 100),
    help="Maximum number of results returned per page",
    default=100,
    show_default=True,
)
@click.option(
    "-v",
    "--by-video-id",
    help="Get all comments for one or a list of videos",
    is_flag=True,
)
@click.option("--name", help="Specify an API key name added to youte config")
@click.option("--key", help="Specify a YouTube API key")
@click.option("--tidy-to", type=click.Path(), help="Parse data and export to file")
@click.option(
    "--format",
    "format_",
    type=click.Choice(["json", "csv"]),
    default="csv",
    help="Format data is parsed into. Can be 'json', 'jsonl', or 'csv'",
    show_default=True,
)
def comments(
    items: list[str],
    outfile: Path,
    output_format: Literal["json", "jsonl"],
    pretty: bool,
    order: Literal["time", "relevance"],
    text_format: Literal["html", "plainText"],
    query: str,
    name: str,
    key: str,
    file_path: Path,
    by_video_id: bool,
    by_channel_id: bool,
    tidy_to: Path,
    format_: Literal["json", "csv"],
    max_results: int,
) -> None:
    """
    Get YouTube comments by video IDs, channel IDs, or thread IDs

    The IDs should all belong to one type, i.e. either video or comment thread.
    You cannot mix both video AND comment thread IDs in one command.

    OUTPUT: name of JSON file to store output

    ITEMS: ID(s) of item as provided by YouTube
    """
    api_key = key if key else _get_api_key(name=name)
    yob = Youte(api_key=api_key)

    vid_ids: list[str] | None = None
    channel_ids: list[str] | None = None
    comment_ids: list[str] | None = None

    if by_video_id:
        vid_ids = _get_ids(items, file_path)
    elif by_channel_id:
        channel_ids = _get_ids(items, file_path)
    else:
        comment_ids = _get_ids(items, file_path)

    results = [
        result
        for result in yob.get_comment_threads(
            video_ids=vid_ids,
            related_channel_ids=channel_ids,
            comment_ids=comment_ids,
            order=order,
            search_terms=query,
            text_format=text_format,
            max_results=max_results,
        )
    ]

    export_file(
        results, outfile, file_format=output_format, pretty=pretty, ensure_ascii=True
    )

    if tidy_to:
        if format_ == "csv":
            parser.parse_comments(results).to_csv(tidy_to)
        elif format_ == "json":
            parser.parse_comments(results).to_json(tidy_to, pretty=pretty)


@youte.command()
@click.argument("items", nargs=-1, required=False)
@click.option(
    "-o",
    "--outfile",
    type=click.Path(),
    help="Name of json file to store results to",
)
@click.option(
    "--output-format",
    default="json",
    type=click.Choice(["json", "jsonl"]),
    help="Format of the output file",
    show_default=True,
)
@click.option("--pretty", "-p", is_flag=True, help="Pretty print JSON")
@click.option("-f", "--file-path", help="Use IDs from file", default=None)
@click.option(
    "--text-format",
    type=click.Choice(["html", "plainText"]),
    default="html",
    show_default=True,
    help="Specify the text format of the returned data",
)
@click.option(
    "--max-results",
    type=click.IntRange(0, 100),
    help="Maximum number of results returned per page",
    default=100,
    show_default=True,
)
@click.option("--name", help="Specify an API key name added to youte config")
@click.option("--key", help="Specify a YouTube API key")
@click.option("--tidy-to", type=click.Path(), help="Parse data and export to file")
@click.option(
    "--format",
    "format_",
    type=click.Choice(["json", "csv"]),
    default="csv",
    help="Format data is parsed into. Can be 'json', 'jsonl', or 'csv'",
    show_default=True,
)
def replies(
    items: list[str],
    outfile: Path,
    output_format: Literal["json", "jsonl"],
    pretty: bool,
    text_format: Literal["html", "plainText"],
    name: str,
    key: str,
    file_path: Path,
    tidy_to: Path,
    format_: Literal["json", "csv"],
    max_results: int,
) -> None:
    """
    Get replies to comment threads using thread IDs

    ITEMS: ID(s) of comment thread
    """
    api_key = key if key else _get_api_key(name=name)
    yob = Youte(api_key=api_key)

    ids = _get_ids(items, file_path)

    results = [
        result
        for result in yob.get_thread_replies(
            thread_ids=ids, text_format=text_format, max_results=max_results
        )
    ]

    export_file(
        results, outfile, file_format=output_format, pretty=pretty, ensure_ascii=True
    )

    if tidy_to:
        if format_ == "csv":
            parser.parse_comments(results).to_csv(tidy_to)
        elif format_ == "json":
            parser.parse_comments(results).to_json(tidy_to, pretty=pretty)


@youte.command()
@click.argument("items", nargs=-1, required=False)
@click.option(
    "-o",
    "--outfile",
    type=click.Path(),
    help="Name of json file to store results to",
)
@click.option(
    "--output-format",
    default="json",
    type=click.Choice(["json", "jsonl"]),
    help="Format of the output file",
    show_default=True,
)
@click.option("--pretty", "-p", is_flag=True, help="Pretty print JSON")
@click.option("-f", "--file-path", help="Get IDs from file", default=None)
@click.option("--name", help="Specify an API key name added to youte config")
@click.option("--key", help="Specify a YouTube API key")
@click.option(
    "--max-results",
    type=click.IntRange(0, 50),
    help="Maximum number of results returned per page",
    default=50,
    show_default=True,
)
@click.option("--tidy-to", type=click.Path(), help="Parse data and export to file")
@click.option(
    "--format",
    "format_",
    type=click.Choice(["json", "csv"]),
    default="csv",
    help="Format data is parsed into. Can be 'json', 'jsonl', or 'csv'",
    show_default=True,
)
def videos(
    items: list[str],
    outfile: Path,
    output_format: Literal["json", "jsonl"],
    pretty: bool,
    file_path: Path,
    name: str,
    key: str,
    tidy_to: Path,
    format_: Literal["json", "jsonl", "csv"],
    max_results: int,
) -> None:
    """Hydrate YouTube resource IDs

    Get all metadata for a list of resource IDs.
    By default, the function hydrates video IDs.

    The IDs should all belong to one type, i.e. either video, channel, or comment.
    For example, you cannot mix both video AND channel IDs in one command.

    OUTPUT: name of JSON file to store output

    ITEMS: ID(s) of items as provided by YouTube
    """
    api_key = key if key else _get_api_key(name=name)
    yob = Youte(api_key=api_key)

    ids = _get_ids(string=items, file=file_path)

    results = [
        result for result in yob.get_video_metadata(ids, max_results=max_results)
    ]

    export_file(
        results, outfile, file_format=output_format, pretty=pretty, ensure_ascii=True
    )

    if tidy_to:
        if format_ == "csv":
            parser.parse_videos(results).to_csv(tidy_to)
        elif format_ == "json":
            parser.parse_videos(results).to_json(tidy_to, pretty=pretty)


@youte.command()
@click.argument("items", nargs=-1, required=False)
@click.option(
    "-o",
    "--outfile",
    type=click.Path(),
    help="Name of json file to store results to",
)
@click.option(
    "--output-format",
    default="json",
    type=click.Choice(["json", "jsonl"]),
    help="Format of the output file",
    show_default=True,
)
@click.option("--pretty", "-p", is_flag=True, help="Pretty print JSON")
@click.option("-f", "--file-path", help="Get IDs from file", default=None)
@click.option("--name", help="Specify an API key name added to youte config")
@click.option("--key", help="Specify a YouTube API key")
@click.option(
    "--max-results",
    type=click.IntRange(0, 50),
    help="Maximum number of results returned per page",
    default=50,
    show_default=True,
)
@click.option("--tidy-to", type=click.Path(), help="Parse data and export to file")
@click.option(
    "--format",
    "format_",
    type=click.Choice(["json", "csv"]),
    default="csv",
    help="Format data is parsed into. Can be 'json', 'jsonl', or 'csv'",
    show_default=True,
)
def channels(
    items: list[str],
    outfile: Path,
    output_format: Literal["json", "jsonl"],
    pretty: bool,
    file_path: Path,
    name: str,
    key: str,
    tidy_to: Path,
    format_: Literal["json", "csv"],
    max_results: int,
) -> None:
    """Hydrate YouTube resource IDs

    Get all metadata for a list of resource IDs.
    By default, the function hydrates video IDs.

    The IDs should all belong to one type, i.e. either video, channel, or comment.
    For example, you cannot mix both video AND channel IDs in one command.

    OUTPUT: name of JSON file to store output

    ITEMS: ID(s) of items as provided by YouTube
    """
    api_key = key if key else _get_api_key(name=name)
    yob = Youte(api_key=api_key)

    ids = _get_ids(string=items, file=file_path)

    results = [
        result for result in yob.get_channel_metadata(ids=ids, max_results=max_results)
    ]

    export_file(
        results, outfile, file_format=output_format, pretty=pretty, ensure_ascii=True
    )

    if tidy_to:
        if format_ == "csv":
            parser.parse_channels(results).to_csv(tidy_to)
        elif format_ == "json":
            parser.parse_channels(results).to_json(tidy_to, pretty=pretty)


@youte.command()
@click.argument("items", nargs=-1, required=False)
@click.option(
    "-f", "--file-path", type=click.Path(), help="Get IDs from file", default=None
)
@click.option(
    "-o",
    "--outfile",
    type=click.Path(),
    help="Name of JSON file to store output",
)
@click.option(
    "--output-format",
    default="json",
    type=click.Choice(["json", "jsonl"]),
    help="Format of the output file",
    show_default=True,
)
@click.option("--pretty", "-p", is_flag=True, help="Pretty print JSON")
@click.option(
    "--safe-search",
    type=click.Choice(["none", "moderate", "strict"], case_sensitive=False),
    help="Include or exclude restricted content",
    default="none",
    show_default=True,
)
@click.option(
    "--region",
    type=click.STRING,
    help="Specify region the videos can be viewed in (ISO 3166-1 alpha-2 country code)",
)
@click.option(
    "--lang",
    help="Return results most relevant to a language (ISO 639-1 two-letter code)",
)
@click.option("--name", help="Specify an API key name added to youte config")
@click.option("--key", help="Specify a YouTube API key")
@click.option(
    "--max-results",
    type=click.IntRange(0, 50),
    help="Maximum number of results returned per page",
    default=50,
    show_default=True,
)
@click.option("--tidy-to", type=click.Path(), help="Parse data and export to file")
@click.option(
    "--format",
    "format_",
    type=click.Choice(["json", "csv"]),
    default="csv",
    help="Format data is parsed into. Can be 'json', 'jsonl', or 'csv'",
    show_default=True,
)
@click.option(
    "--max-pages",
    "-m",
    type=click.INT,
    help="Maximum number of result pages to retrieve",
)
def related_to(
    items: list[str],
    outfile: Path,
    output_format: Literal["json", "jsonl"],
    pretty: bool,
    safe_search: Literal["none", "moderate", "strict"],
    region: str,
    lang: str,
    file_path: str,
    name: str,
    key: str,
    max_results: int,
    max_pages: int,
    tidy_to: Path,
    format_: Literal["json", "csv"],
):
    """Get videos related to a video

    ITEMS: ID(s) of videos as provided by YouTube
    """
    api_key = key if key else _get_api_key(name=name)
    yob = Youte(api_key=api_key)

    ids = _get_ids(string=items, file=file_path)

    results = [
        result
        for result in yob.get_related_videos(
            video_ids=ids,
            region=region,
            relevance_language=lang,
            safe_search=safe_search,
            max_results=max_results,
            max_pages_retrieved=max_pages,
        )
    ]

    export_file(
        results, outfile, file_format=output_format, pretty=pretty, ensure_ascii=True
    )

    if tidy_to:
        if format_ == "csv":
            parser.parse_searches(results).to_csv(tidy_to)
        elif format_ == "json":
            parser.parse_searches(results).to_json(tidy_to)


@youte.command()
@click.option(
    "-o",
    "--outfile",
    type=click.Path(),
    help="Name of JSON file to store output",
)
@click.option(
    "--output-format",
    default="json",
    type=click.Choice(["json", "jsonl"]),
    help="Format of the output file",
    show_default=True,
)
@click.option("--pretty", "-p", is_flag=True, help="Pretty print JSON")
@click.option(
    "-r",
    "--region-code",
    help="ISO 3166-1 alpha-2 country codes to retrieve videos",
    default="us",
    show_default=True,
)
@click.option(
    "--video-category",
    help="Video category ID for which the most popular videos should be retrieved",
)
@click.option("--name", help="Specify an API key name added to youte config")
@click.option("--key", help="Specify a YouTube API key")
@click.option(
    "--max-results",
    type=click.IntRange(0, 50),
    help="Maximum number of results returned per page",
    default=50,
    show_default=True,
)
@click.option("--tidy-to", type=click.Path(), help="Parse data and export to file")
@click.option(
    "--format",
    "format_",
    type=click.Choice(["json", "csv"]),
    default="csv",
    help="Format data is parsed into. Can be 'json' or 'csv'",
    show_default=True,
)
def chart(
    region_code: str,
    outfile: Path,
    output_format: Literal["json", "jsonl"],
    pretty: bool,
    video_category: str,
    name: str,
    key: str,
    tidy_to: Path,
    format_: Literal["json", "jsonl", "csv"],
    max_results: int,
):
    """Return the most popular videos for a region and video category

    By default, if nothing is else is provided, the command retrieves the most
    popular videos in the US.

    OUTPUT: name of JSON file to store results
    """

    api_key = key if key else _get_api_key(name=name)
    yob = Youte(api_key=api_key)

    results = [
        result
        for result in yob.get_most_popular(
            region_code=region_code,
            video_category_id=video_category,
            max_results=max_results,
        )
    ]

    export_file(
        results, outfile, file_format=output_format, pretty=pretty, ensure_ascii=True
    )

    if tidy_to:
        if format_ == "csv":
            parser.parse_videos(results).to_csv(tidy_to)
        elif format_ == "json":
            parser.parse_videos(results).to_json(tidy_to, pretty=pretty)


@youte.command()
@click.argument("infile", type=click.Path())
@click.option(
    "-o", "--output", type=click.File(mode="w"), help="Output text file to store IDs in"
)
def dehydrate(infile: Path, output: IO) -> None:
    """Extract an ID list from a file of YouTube resources

    INFILE: JSON file of YouTube resources
    """
    try:
        ids = retrieve_ids_from_file(infile)
        for id_ in ids:
            click.echo(id_, file=output)
    except JSONDecodeError:
        logging.exception("Error occurred")
        raise click.BadParameter("File is not JSON.")


@youte.group()
def config():
    """
    Set up API keys to access data from YouTube API
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

    config_file_path = Path(_get_config_path())

    if not config_file_path.parent.exists():
        click.echo()
        click.secho(
            "Creating config folder at %s" % config_file_path.parent, fg="magenta"
        )
        config_file_path.parent.mkdir(parents=True)

    conf = _set_up_config()
    click.echo(f"Config file is stored at {config_file_path.resolve()}.")

    try:
        conf.add_profile(name=username, key=api_key)
    except ValueAlreadyExists:
        raise click.BadArgumentUsage("API key already exists in config file.")

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
            - `youte config list-keys` to see the list of registered keys.
            - `youte config add-key to add a new API key.
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

    if not Path(_get_config_path()).exists():
        click.echo("No API key has been added to config file.")
    else:
        for name in conf:
            if "default" in conf[name]:
                click.secho("%s -------- %s (*)" % (name, conf[name]["key"]), fg="blue")
            else:
                click.echo("%s -------- %s" % (name, conf[name]["key"]))
        click.echo()
        click.secho(
            "All API keys are stored in %s" % _get_config_path(), fg="green", bold=True
        )
        click.echo()


def _get_config_path(filename="config"):
    config_file_path = Path(click.get_app_dir("youte")).joinpath(filename)
    return str(config_file_path)


def _set_up_config(filename=_get_config_path()) -> YouteConfig:
    config_file = YouteConfig(filename=filename)
    return config_file


def _get_ids(string: list[str] = None, file: str | Path = None) -> list[str]:
    if not (string or file):
        raise click.BadParameter("No ids are specified.")
    if string:
        ids = list(string)
    if file:
        with open(file, mode="r") as f:
            ids = [row.rstrip() for row in f.readlines()]
    return ids


def _get_api_key(name=None, filename="config"):
    """Get API key from config file.
    If no name is given, use default API key
    """
    logger.info("Getting API key from config file.")
    config_file_path = Path(click.get_app_dir("youte")).joinpath(filename)
    config_obj = YouteConfig(filename=str(config_file_path))

    if name:
        try:
            api_key = config_obj[name]["key"]
        except KeyError:
            click.secho("ERROR", fg="red", bold=True)
            click.secho(
                "No API key found for %s. Did you use a different name?\n"
                "Try:\n"
                "`youte config list-keys` to get a "
                "full list of registered API keys "
                "or `youte config add-key` to add a new API key" % name,
                fg="red",
                bold=True,
            )
            sys.exit(1)
    else:
        default_check = []
        for name in config_obj:
            if "default" in config_obj[name]:
                default_check.append(name)
        if not default_check:
            click.secho(
                "No API key name was specified, and you haven't got a default API key.",
                fg="red",
                bold=True,
            )
            sys.exit(1)
        else:
            api_key = config_obj[default_check[0]]["key"]

    return api_key
