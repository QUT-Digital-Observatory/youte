import logging
import pathlib
import configobj

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

        self[name]['default'] = True
        self.write()
        logger.info(f"Set {name} as the default key...")



