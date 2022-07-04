"""
Copyright: Digital Observatory 2022 <digitalobservatory@qut.edu.au>
Author: Boyd Nguyen <thaihoang.nguyen@qut.edu.au>

Required Setup:

A YouTube API key needs to be present in the YOUTUBE_API_KEY environment variable.

"""

import os
import logging
import click
from pathlib import Path

from youtupy import collector, databases
from youtupy.process import process_to_database
from youtupy.collector_class import SearchCollector
from youtupy.config import YoutubeConfig

# Logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

formatter = logging.Formatter(
    '%(asctime)s - %(module)s: %(message)s (%(levelname)s)'
)

console_handler.setFormatter(formatter)

logger.addHandler(console_handler)


# CLI argument set up:
@click.group()
def youtupy():
    pass


@youtupy.command()
@click.argument("dbpath", required=True)
@click.option("-q", "--query", help="Search query")
@click.option("-s", "--start", help="Start date (YYYY-MM-DD)")
@click.option("-e", "--end", help="End date (YYYY-MM-DD)")
@click.option("--max-quota", default=10000,
              help="Maximum quota allowed",
              show_default=True)
@click.option("-v", "--video", is_flag=True,
              help="Get enriching video information")
@click.option("-c", "--channel", is_flag=True,
              help="Get enriching channel information")
@click.option("--api-key", envvar='YOUTUBE_API_KEY')
def collect(dbpath, api_key, query, start, end, max_quota, video, channel):
    """Collect data from Youtube API.
    Can add key to a YOUTUBE_API_KEY environment variable.
    """
    if os.path.exists(dbpath):

        flag = input(
            """
            This database already exists.
            Continue with this database? [Y/N]
            """).lower()

        if flag == 'y':
            logger.info(f"Updating existing database {dbpath}...")
            pass

        if flag == 'n':
            dbpath = input("Type the name of the new database to be created: ")

    databases.initialise_database(path=dbpath)

    databases.validate_metadata(path=dbpath,
                                input_query=query,
                                input_start=start,
                                input_end=end)

    collector.collect(endpoint='search',
                      dbpath=dbpath,
                      key=api_key,
                      max_quota=max_quota,
                      q=query,
                      publishedAfter=start,
                      publishedBefore=end)

    if video:
        collector.collect(endpoint='video',
                          dbpath=dbpath,
                          key=api_key,
                          max_quota=max_quota)

    if channel:
        collector.collect(endpoint='channel',
                          dbpath=dbpath,
                          key=api_key,
                          max_quota=max_quota)


@youtupy.command()
def init():
    click.secho('Welcome to youtupy!', fg='green', bold=True)
    click.echo()
    click.echo('To get started, an API key is required to get data '
               'from Youtube API.')
    click.echo()
    click.echo('To obtain an API key, follow the steps in')
    click.echo('https://developers.google.com/youtube/v3/getting-started.')
    click.echo()
    click.echo('Setting up you Youtube configuration')
    click.echo()
    api_key = click.prompt('Enter your API key')
    username = click.prompt('Enter a name for this key')

    config = YoutubeConfig(filename='config')
    config_path = Path(config.file_path)
    click.echo(f'File is at {config_path.resolve()}')

    pass



if __name__ == "__main__":
    collect()