"""
Copyright: Digital Observatory 2022 <digitalobservatory@qut.edu.au>
Author: Boyd Nguyen <thaihoang.nguyen@qut.edu.au>

Collect Youtube videos matching specified keywords from Youtube API.

This script does the following:

1. Get Youtube search results (videos) matching specified keywords
2. Use search results to get enriching data on videos (e.g. full video description, view counts)
3. Use search results to get enriching data on channels (e.g. channel title, channel description)
4. Process all raw responses into clean data
4. Export clean data to csv if specified
5. Handle YouTube API quota limit
6. Ensure one database only stores one particular collection, so if you start collecting
another collection (i.e. different keywords or date range) into the same database
an error will be raised.

Required libraries:

- requests
- python-dotenv
- dateutils

Required Setup:

A YouTube API key needs to be present in the YOUTUBE_API_KEY environment variable.

"""

import os
import sqlite3
import argparse
import logging

from youtupy import databases, collector

# Logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

file_handler = logging.FileHandler('youtube.log')
file_handler.setLevel(logging.WARNING)

formatter = logging.Formatter('%(asctime)s - %(levelname)s: %(message)s')
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

logger.addHandler(console_handler)
logger.addHandler(file_handler)

# CLI argument set up:
# if __name__ == "__main__": (put all CLI config under this)
parser = argparse.ArgumentParser(description="""
        Collect Youtube videos containing 'critical race theory'
        through Youtube API and store raw responses in a SQLite database.

        Requires a YOUTUBE_API_KEY environment variable, which can be put in
        an ".env" folder. Do in shell:

            echo YOUTUBE_API_KEY=<insert key here> > .env

        The script also creates another database to keep track of quota usage so that
        we avoid exceeding Youtube's limit of 10,000 units.
        """,
                                 formatter_class=argparse.RawTextHelpFormatter)

parser.add_argument("dbpath", help="Path to database file. Must end in `.db`.")
parser.add_argument("-q", "--query", help="Search query")
parser.add_argument("-s", "--start", help="Start date (YYYY-MM-DD)")
parser.add_argument("-e", "--end", help="End date (YYYY-MM-DD)")
parser.add_argument("--qpath", help="Path to the quota database. Default value: youtube_quota.db",
                    default="youtube_quota.db")
parser.add_argument("-m", "--max",
                    help="Max quota. Default value: 9000. Must be product of 100. Maximum value allowed is 9500.",
                    default=9000, type=int)
parser.add_argument(
    "-v", "--video", help="Get enriching video information", action="store_true")
parser.add_argument(
    "-c", "--channel", help="Get enriching channel information", action="store_true")
parser.add_argument(
    "--to-csv", help="Export to a csv file, of the same name as the database", action="store_true")
args = parser.parse_args()

dbpath = args.dbpath
publishedAfter = args.start
publishedBefore = args.end
quota_dbpath = args.qpath
max_quota = args.max

search_query = args.query

# Check if database exists
# leave this in here - checking input
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

# function in database.py
databases.initialise_database(path=dbpath)

db = sqlite3.connect(dbpath)

databases.validate_metadata(path=dbpath,
                            input_query=args.query,
                            input_start=args.start,
                            input_end=args.end)

collector.collect(endpoint=args.search,
                  dbpath=dbpath,
                  q=search_query,
                  publishedAfter=args.start,
                  publishedBefore=args.end)




# STEP 6. Combine everything together and export to csv

# # another module but probs not confined to csv
# if args.to_csv:
#     logging.info("Exporting data...")
#
#     full_data = db.execute(
#         """
#         select video_id, published_at, title, description, topic_categories, upload_status, view_count, like_count, comment_count,
#         channel_title, videos.channel_id, ch_published_at, ch_description, ch_topic_categories, ch_view_count, ch_subscriber_count, ch_video_count
#         from videos
#         left join channels
#         on videos.channel_id = channels.channel_id;
#         """
#     )
#
#     headers = ["video_id", "published_at", "title", "description", "topic_categories", "upload_status", "view_count",
#                "like_count", "comment_count",
#                "channel_title", "channel_id", "ch_published_at", "ch_description", "ch_topic_categories",
#                "ch_view_count",
#                "ch_subscriber_count", "ch_video_count"]
#
#     with open(f'{dbpath[:-3]}.csv', 'w', newline='', encoding="utf-8") as csvfile:
#         writer = csv.writer(csvfile)
#         writer.writerow(headers)
#         writer.writerows(full_data)
