"""
Copyright: Digital Observatory 2022 <digitalobservatory@qut.edu.au>
Author: Boyd Nguyen <thaihoang.nguyen@qut.edu.au>
"""
import logging
import click
from pathlib import Path

from youtupy.collector import SearchCollector
from youtupy.config import YoutubeConfig
from youtupy.quota import Quota

# Logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# console_handler = logging.StreamHandler()
# console_handler.setLevel(logging.INFO)
# console_formatter = logging.Formatter('%(message)s')
# console_handler.setFormatter(console_formatter)

file_handler = logging.FileHandler('youtupy.log')
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter(
    '%(asctime)s - %(module)s: %(message)s (%(levelname)s)'
)
file_handler.setFormatter(file_formatter)

# logger.addHandler(console_handler)
logger.addHandler(file_handler)


# CLI argument set up:
@click.group()
def youtupy():
    """
    Utility to collect YouTube video meta-data and comments via YouTube API.
    Run `youtupy configure --help` to get started.
    """
    pass


@youtupy.command()
@click.argument("query", required=True)
@click.option("-o", "--output", help="Output database. Must end in `.db`")
@click.option("--from", "from_", help="Start date (YYYY-MM-DD)")
@click.option("--to", help="End date (YYYY-MM-DD)")
@click.option("--max-quota", default=10000,
              help="Maximum quota allowed",
              show_default=True)
@click.option("--name", help="Name of the API key (optional)")
@click.option("--comments", help="Get video comments", is_flag=True)
@click.option("--replies", help="Get replies to video comments", is_flag=True)
def search(output,
           name,
           query,
           from_,
           to,
           max_quota,
           comments=False,
           replies=False):
    """Collect data from Youtube API.
    """

    click.secho("Getting API key from config file.",
                fg='magenta')
    config_file_path = Path(click.get_app_dir('youtupy')).joinpath('config')
    config = YoutubeConfig(filename=str(config_file_path))

    if name:
        try:
            api_key = config[name]['key']
        except KeyError:
            raise KeyError("No API key found for %s. "
                           "Did you use a different name? "
                           "Try: "
                           "`youtupy init list-keys` to get a "
                           "full list of registered API keys "
                           "or `youtupy init add-key` to add a new API key"
                           % name
            )
    else:
        default_check = []
        for name in config:
            if 'default' in config[name]:
                default_check.append(name)
        if not default_check:
            raise KeyError("No API key name was specified, and "
                           "you haven't got a default API key.")
        else:
            api_key = config[default_check[0]]['key']

    click.secho("Setting up collector...",
                fg='magenta')
    clt = SearchCollector(api_key=api_key, max_quota=max_quota)
    clt.add_param(q=query)
    if from_:
        clt.add_param(publishedAfter=from_)
    if to:
        clt.add_param(publishedBefore=to)

    quota = Quota(api_key=api_key, config_path=str(config_file_path))
    clt.add_quota(quota=quota)
    clt.run(dbpath=output)
    clt.get_enriching_data(endpoint='video')
    clt.get_enriching_data(endpoint='channel')

    if comments:
        clt.get_comments(replies=replies)

    click.echo()
    click.secho(f'All data is stored in {output}.\n'
                f'Schema:\n'
                f'  - search_results\n'
                f'  - videos\n'
                f'  - channels',
                fg='cyan',
                bold=True)
    if comments:
        click.secho('  - comment_threads',
                    fg='cyan',
                    bold=True)
    if replies:
        click.secho(' - replies',
                    fg='cyan',
                    bold=True)


@youtupy.group()
def configure():
    """
    Set up API keys to access data from YouTube API.
    """


@configure.command()
def add_key():
    """
    Add YouTube API key
    """
    click.secho('Welcome to youtupy! 👋', fg='green', bold=True)
    click.echo('Configuring your profile...')
    click.echo()
    click.echo('To get started, an API key is required to get data '
               'from Youtube API.')
    click.echo()
    click.echo('To obtain an API key, follow the steps in')
    click.echo('https://developers.google.com/youtube/v3/getting-started.')
    click.echo()
    click.echo('Once you have an API key, run `youtupy init add-key` to start.')

    click.secho('Setting up you Youtube configuration...',
                fg='magenta')
    click.echo()
    api_key = click.prompt('Enter your API key')
    username = click.prompt('Enter a name for this key')

    config_file_path = Path(click.get_app_dir('youtupy')).joinpath('config')

    if not config_file_path.parent.exists():
        click.echo('Creating config folder at %s' % config_file_path.parent)
        config_file_path.parent.mkdir(parents=True)

    config = YoutubeConfig(filename=str(config_file_path))
    click.echo()
    click.echo(f'Config file is stored at {config_file_path.resolve()}.')

    config.add_profile(name=username, key=api_key)

    if click.confirm('Set this API key as default?'):
        config.set_default(username)
    click.echo()
    click.secho('API key successfully configured!',
                fg='green',
                bold=True)
    click.echo()
    click.echo('To add more API keys, rerun `youtupy init add-key`.')
    click.echo('To set an API key as default, run `youtupy init set-default'
               '<name-of-key>')


@configure.command()
@click.argument('name')
def set_default(name):
    """Set default API key"""
    click.echo('Setting %s as default key' % name)
    config_file_path = Path(click.get_app_dir('youtupy')).joinpath('config')
    config = YoutubeConfig(filename=str(config_file_path))
    config.set_default(name)
    click.echo('%s is now your default API key.' % config[name]['key'])


@configure.command()
def list_keys():
    """Show a list of keys already added"""
    click.echo()
    config_file_path = Path(click.get_app_dir('youtupy')).joinpath('config')
    config = YoutubeConfig(filename=str(config_file_path))

    for name in config:
        if 'default' in config[name]:
            click.secho('%s -------- %s (*)' % (name, config[name]['key']),
                        fg='blue')
        else:
            click.echo('%s -------- %s' % (name, config[name]['key']))
    click.echo()
    click.secho('All API keys are stored in %s' % config_file_path,
                fg='green',
                bold=True)
    click.echo()
