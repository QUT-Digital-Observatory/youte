import logging
from pathlib import Path

import click
import configobj

from youte.exceptions import ValueAlreadyExists

logger = logging.getLogger(__name__)


class YouteConfig(configobj.ConfigObj):
    def __init__(self, filename):
        super(YouteConfig, self).__init__(filename)
        self.file_path = filename

    def add_profile(self, name, key):
        existing = []

        try:
            for profile in self:
                existing.append(self[profile]["key"])
        except ValueError:
            pass

        if key in existing:
            raise ValueAlreadyExists("API key already exists.")

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
    logger.info("Getting API key from config file.")
    config_file_path = Path(click.get_app_dir("youte")).joinpath(filename)
    config = YouteConfig(filename=str(config_file_path))

    if name:
        try:
            api_key = config[name]["key"]
        except KeyError:
            raise NoAPINameFound
    else:
        default_check = []
        for name in config:
            if "default" in config[name]:
                default_check.append(name)
        if not default_check:
            raise NoAPIKey
        else:
            api_key = config[default_check[0]]["key"]

    return api_key


def get_config_path(filename="config"):
    config_file_path = Path(click.get_app_dir("youte")).joinpath(filename)
    return str(config_file_path)


class NoAPINameFound(Exception):
    def __str__(self):
        return "No API key found for specified name."


class NoAPIKey(Exception):
    pass