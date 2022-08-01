import logging
from pathlib import Path
import configobj
import click

logger = logging.getLogger(__name__)


class YoutubeConfig(configobj.ConfigObj):
    def __init__(self, filename):
        super(YoutubeConfig, self).__init__(filename)
        self.file_path = filename

    def add_profile(self, name, key):
        self[name] = {}
        self[name]['key'] = key
        self.write()
        logger.info(f"Add key to config file {self.filename}.")

    def set_default(self, name):
        for profile in self:
            if 'default' in self[profile]:
                del self[profile]['default']

        try:
            self[name]['default'] = True
            self.write()
            logger.info('%s is now the default API key.' % name)
        except KeyError:
            logger.error(
                """No such name found.
                You might not have added this profile or 
                added it under a different name.
                Run:
                - `youtupy init list-keys` to see the list of registered keys.
                - `youtupy init add-key to add a new API key.
                """)


def get_api_key(name=None, filename='config'):
    click.secho("Getting API key from config file.",
                fg='magenta')
    config_file_path = Path(click.get_app_dir('youtupy')).joinpath(filename)
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

    return api_key


def get_config_path(filename='config'):
    config_file_path = Path(click.get_app_dir('youtupy')).joinpath(filename)
    return str(config_file_path)