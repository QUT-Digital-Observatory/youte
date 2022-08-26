from datetime import datetime, timedelta
import logging
from dateutil import tz
import time
from pathlib import Path
import click

from youte.config import YouteConfig
from youte.exceptions import InvalidFileName

logger = logging.getLogger(__name__)


class Quota:
    def __init__(
        self, api_key, config_path, units=None, created_utc=None, reset_remaining=None
    ):
        self.units = units
        self.api_key = api_key
        self._created_utc = created_utc
        self.reset_remaining = reset_remaining
        self.config_path = config_path

    @property
    def created_utc(self):
        return self._created_utc

    @created_utc.setter
    def created_utc(self, value):
        if isinstance(value, datetime) or value is None:
            self._created_utc = value
        else:
            raise TypeError("created_utc must be a datetime object.")

    def get_quota(self):
        full_path = Path(self.config_path).resolve()

        logger.debug("Getting quota usage from %s" % full_path)

        if not full_path.exists():
            raise InvalidFileName("Config file not found.")

        config = YouteConfig(str(full_path))

        for profile in config:
            if config[profile]["key"] == self.api_key:
                name = profile

        if "name" not in locals():
            raise KeyError(
                "No profile for key %s found."
                "Configure your API key first with `youte init`."
            )

        if "units" not in config[name]:
            self.units = 0
            self.created_utc = None
        else:
            quota = int(config[name]["units"])
            timestamp = datetime.fromisoformat(config[name]["created_utc"])

            # get midnight Pacific time
            now_pt = datetime.now(tz=tz.gettz("US/Pacific"))
            midnight_pt = now_pt.replace(hour=0, minute=0, second=0, microsecond=0)

            if timestamp > midnight_pt:
                logger.debug(f"Quota found, {quota} units have been used.")
                self.units = quota
                self.created_utc = timestamp
                self.reset_remaining = _get_reset_remaining(timestamp)

            else:
                logger.debug("Quota has been reset to 0.")
                self.units = 0
                self.created_utc = None

    def add_quota(self, unit_costs, created_utc):
        self.units += unit_costs
        self.created_utc = created_utc

        full_path = Path(self.config_path).resolve()

        logger.debug("Getting quota usage from %s" % full_path)

        if not full_path.exists():
            raise InvalidFileName("Config file not found.")

        else:
            config = YouteConfig(str(full_path))

            for profile in config:
                if config[profile]["key"] == self.api_key:
                    name = profile

            if "name" not in locals():
                raise KeyError(
                    "No profile for key %s found."
                    "Configure your API key first "
                    "with `youte init`." % self.api_key
                )

            else:
                config[name]["units"] = self.units
                config[name]["created_utc"] = self.created_utc
                config.write()

    def handle_limit(self, max_quota):
        """
        If max quota has been reached, sleep until reset time.
        """
        if self.units > max_quota:
            logger.warning("Max quota reached.")
            click.echo("Max quota reached.")

            sleep = _get_reset_remaining(datetime.now(tz=tz.UTC))
            logger.warning(f"Sleeping for {sleep} seconds...")
            click.echo(f"Sleeping for {sleep} seconds...")

            time.sleep(sleep)
            time.sleep(2)
        else:
            pass


def _get_reset_remaining(current) -> int:
    next_reset = datetime.now(tz=tz.gettz("US/Pacific")) + timedelta(days=1)
    next_reset = next_reset.replace(hour=0, minute=0, second=0, microsecond=0)

    reset_remaining = next_reset - current

    return reset_remaining.seconds + 1
