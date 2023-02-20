import logging
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
