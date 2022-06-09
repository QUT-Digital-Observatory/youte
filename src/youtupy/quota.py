import os
import sqlite3
from datetime import datetime, timedelta
import logging
from dateutil import tz
import time

logger = logging.getLogger(__name__)


class Quota:
    def __init__(self, api_key, units=None,
                 created_utc=None, reset_remaining=None):
        self.units = units
        self.api_key = api_key
        self._created_utc = created_utc
        self.reset_remaining = reset_remaining
        _init_quotadb()

    @property
    def created_utc(self):
        return self._created_utc

    @created_utc.setter
    def created_utc(self, value):
        if isinstance(value, datetime) or value is None:
            self._created_utc = value
        else:
            raise TypeError("created_utc must be a datetime object.")

    def get_quota(self, path='quota.db'):
        full_path = '.quota/{}'.format(path)

        logger.debug("Getting quota usage from {}.".format(full_path))

        if not os.path.exists(full_path):
            _init_quotadb(path)

        db = sqlite3.connect(full_path)

        quota_data = [(row[0], row[1])
                      for row in
                      db.execute("""
                        select quota, timestamp from quota
                        where api_key = ?
                        """,
                                 (self.api_key,))
                      ]

        if not quota_data:
            logger.debug("No quota data found. Setting quota as 0.")

            self.units = 0
            self.created_utc = None
        else:
            quota, timestamp = quota_data[0]
            timestamp = datetime.fromisoformat(timestamp)

            # get midnight Pacific time
            now_pt = datetime.now(tz=tz.gettz('US/Pacific'))
            midnight_pt = now_pt.replace(hour=0, minute=0, second=0,
                                         microsecond=0)

            if timestamp > midnight_pt:
                logger.debug(
                    f"Quota data found, {quota} units have been used.")

                self.units = quota
                self.created_utc = timestamp
                self.reset_remaining = _get_reset_remaining(timestamp)

            else:
                logger.debug("Quota has been reset to 0.")

                self.units = 0
                self.created_utc = None

    def add_quota(self, unit_costs, created_utc, path='.quota/quota.db'):
        self.units += unit_costs
        self.created_utc = created_utc

        with sqlite3.connect(path) as db:
            db.execute(
                """
                replace into quota(quota, timestamp, api_key) 
                    values (?,?,?)
                """,
                (self.units, created_utc, self.api_key))

    def handle_limit(self, max_quota):
        """
        If max quota has been reached, sleep until reset time.
        """
        if self.units > max_quota:
            logger.warning("Max quota reached.")

            sleep = _get_reset_remaining(datetime.now(tz=tz.UTC))
            logger.warning(f"Sleeping for {sleep} seconds...")

            time.sleep(sleep)
            time.sleep(2)
        else:
            pass


def _init_quotadb(path='quota.db'):
    if not os.path.exists('.quota'):
        os.mkdir('.quota')
    db = sqlite3.connect(".quota/{}".format(path))
    db.execute(
        """
        create table if not exists quota(
            /*
            This records the running Youtube quota used everyday.
            One row matches one API key.
            */
            api_key primary key,
            quota,          
            timestamp
            );
        """)


def _get_reset_remaining(current) -> int:
    next_reset = datetime.now(tz=tz.gettz('US/Pacific')) + timedelta(days=1)
    next_reset = next_reset.replace(hour=0, minute=0, second=0, microsecond=0)

    reset_remaining = next_reset - current

    return reset_remaining.seconds + 1


print("Done")
