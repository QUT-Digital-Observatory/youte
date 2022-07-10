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
        try:
            self[name]['default'] = True
            self.write()
        except KeyError:
            logger.error(
                """No such name found. 
                You might not have added this profile or 
                added it under a different name.
                Run `youtupy init list-keys` to see the list of registered keys.
                Run `youtupy init add-key to add a new API key.
                """)

        logger.info(f"Set {name} as the default key...")
