import logging
from pathlib import Path
import configobj
import click
import sys

logger = logging.getLogger(__name__)


class YouteConfig(configobj.ConfigObj):
    def __init__(self, filename):
        super(YouteConfig, self).__init__(filename)
        self.file_path = filename

    def add_profile(self, name, key):
        self[name] = {}
        self[name]["key"] = key
        self.write()
        logger.info(f"Add key to config file {self.filename}.")

    def delete_profile(self, name):
        try:
            del self[name]
            self.write()
        except KeyError:
            raise KeyError(f"{name} not found.")


    def set_default(self, name):
        for profile in self:
            if "default" in self[profile]:
                del self[profile]["default"]

        try:
            self[name]["default"] = True
            self.write()
            logger.info("%s is now the default API key." % name)
        except KeyError:
            raise KeyError(f"{name} not found.")


def get_api_key(name=None, filename="config"):
    """Get API key from config file.
    If no name is given, use default API key
    """
    click.secho("Getting API key from config file.", fg="magenta")
    config_file_path = Path(click.get_app_dir("youte")).joinpath(filename)
    config = YouteConfig(filename=str(config_file_path))

    if name:
        try:
            api_key = config[name]["key"]
        except KeyError:
            click.secho("ERROR", fg="red", bold=True)
            click.secho(
                "No API key found for %s. Did you use a different name?\n"
                "Try:\n"
                "`youte init list-keys` to get a "
                "full list of registered API keys "
                "or `youte init add-key` to add a new API key" % name,
                fg="red",
                bold=True,
            )
            sys.exit()
    else:
        default_check = []
        for name in config:
            if "default" in config[name]:
                default_check.append(name)
        if not default_check:
            click.secho(
                "No API key name was specified, and "
                "you haven't got a default API key.",
                fg="red",
                bold=True,
            )
            sys.exit()
        else:
            api_key = config[default_check[0]]["key"]

    return api_key


def get_config_path(filename="config"):
    config_file_path = Path(click.get_app_dir("youte")).joinpath(filename)
    return str(config_file_path)
