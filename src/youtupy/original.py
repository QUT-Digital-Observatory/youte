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
from dotenv import load_dotenv
import sqlite3
import argparse
import logging
import time
import requests
from datetime import datetime, timedelta
import json
import random
import html
import csv
from dateutil import tz

# SETUP

# Get environment variables from env file
load_dotenv('.env')

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

# API endpoints and quota costs
# youtube module that does API requests - put this there
url = {
    'search': r"https://www.googleapis.com/youtube/v3/search",
    'video': r"https://www.googleapis.com/youtube/v3/videos",
    'channel': r"https://www.googleapis.com/youtube/v3/channels"
}

# move to quota.py
quota_cost = {
    'search': 100,
    'video': 1,
    'channel': 1
}

search_query = args.query

# Check if database exists
# leave this in here - checking input
if os.path.exists(dbpath):

    flag = input(
        "This database already exists. Continue with this database? [Y/N]").lower()

    if flag == 'y':
        logger.info(f"Updating existing database {dbpath}...")
        pass

    if flag == 'n':
        dbpath = input("Type the name of the new database to be created: ")

# function in database.py
db = sqlite3.connect(dbpath)
quota_db = sqlite3.connect(quota_dbpath)

# Create a table to store api responses
quota_db.executescript("""
        create table if not exists quota(
            /*
            This records the running Youtube quota used everyday. There should be only one row.
            */
            id primary key check (id = 0) not null,
            quota,
            timestamp
            );
            """)

# STEP 1. CONDUCT SEARCH VIA YOUTUBE SEARCH ENDPOINT

# Create tables to store api responses and metadata of search
# put in database.py
db.executescript(
    """
    create table if not exists search_api_response(
                /*
                This table records the requests made to Youtube API Search endpoint.
                Each row represents a URL of the request made.

                If a request has not been made, it won't be in this database.
                */
                next_page_token primary key,
                request_url text,
                status_code integer,
                response json,
                total_results,
                retrieval_time
                );

    create table if not exists meta_data(
        /*
        This records all the meta data about the collection.
        As one database should contain only one collection of a specific date range,
        this table should only have one row.
        */
        id primary key check (id = 0),
        query,
        publishedAfter,
        publishedBefore
        );
    """)

# Check the meta_data table to see if data already exist.
# This is to make sure one database contains only one collection with one set of parameters

# database.py - as a function validate criteria to make sure one db contains one collection; call it here
with db:
    existing_data = [(row[0], row[1]) for row in db.execute(
        "select publishedAfter, publishedBefore from meta_data")]

    if existing_data:
        start, end = existing_data[0]
        if start != publishedAfter or end != publishedBefore:
            raise Exception(
                """
                A database can only contain one collection of the same metadata.
                Meta data already exist and do not match input. Check metadata.
                """)

    elif not existing_data:
        db.execute("insert into meta_data(id, query, publishedAfter, publishedBefore) values (?,?,?,?)",
                   (0, search_query, publishedAfter, publishedBefore))

# set up quota database to keep track of API usage
quota_db = sqlite3.connect(quota_dbpath)
quota_db.execute("""
            create table if not exists quota(
                /*
                This records the running Youtube quota used everyday. There should be only one row.
                */
                id primary key check (id = 0) not null,
                quota,
                timestamp
                );
                """)


# check quota in database, if a quota doesn't exist set it to 0. If a quota is past midnight Pacific Time, reset it to 0

def check_quota(qb):
    logger.info("Getting quota usage.")
    quota_data = [(row[0], row[1])
                  for row in qb.execute("select quota, timestamp from quota")]

    if not quota_data:
        logger.info("No quota data found. Setting quota as 0.")
        quota_units = 0
        timestamp = None
    else:
        quota, timestamp = quota_data[0]
        # get midnight Pacific time
        now_pt = datetime.now(tz=tz.gettz('US/Pacific'))
        midnight_pt = now_pt.replace(hour=0, minute=0, second=0, microsecond=0)
        timestamp = datetime.fromisoformat(timestamp)

        if timestamp > midnight_pt:
            logger.info(f"Quota data found, {quota} units have been used.")
            quota_units = quota
        else:
            logger.info("Quota has been reset to 0.")
            quota_units = 0

    return quota_units, timestamp


def handle_limit(units, max_quota, quota_last_time):
    """
    If max quota has been reached, sleep until reset time.
    """
    if units > max_quota:
        logger.info("Max quota reached.")
        next_reset = datetime.now(tz=tz.gettz(
            'US/Pacific')) + timedelta(days=1)
        next_reset = next_reset.replace(
            hour=0, minute=0, second=0, microsecond=0)
        sleep_time = next_reset - datetime.now(tz=tz.UTC)
        logger.info(f"Sleeping for {sleep_time.seconds} seconds...")
        time.sleep(sleep_time.seconds)
        time.sleep(2)
    else:
        pass


# run collector for search results
# this essentially loops through the result pages until there is no page left and no result to retrieve

# put the whole thing as a function in youtube.py
logger.info(
    f"Starting querying Youtube search results. Quota unit cost will be {quota_cost['search']}.")
while True:
    with db:
        # insert empty string for the base request url, if it doesn't already exist
        db.execute(
            "insert or ignore into search_api_response(next_page_token) values ('')")

        # get list of unrecorded page tokens
        logger.info("Getting data from database.")
        to_retrieve = set(
            row[0]
            for row in db.execute("select next_page_token from search_api_response where retrieval_time is null")
        )

    if not len(to_retrieve):
        logger.info("No more data to query.")
        break

    units, quota_last_time = check_quota(quota_db)

    handle_limit(units=units, max_quota=max_quota,
                 quota_last_time=quota_last_time)

    search_params = {
        'part': 'snippet',
        'maxResults': 50,
        'q': search_query,
        'type': 'video',
        'fields': 'pageInfo,prevPageToken,nextPageToken,items(id, snippet(publishedAt, channelId, title, '
                  'description, channelTitle))',
        'order': 'date',
        'safeSearch': 'none',
        'key': os.environ['YOUTUBE_API_KEY']
    }

    if publishedAfter:
        search_params['publishedAfter'] = f"{publishedAfter}T00:00:00Z"
    if publishedBefore:
        search_params['publishedBefore'] = f"{publishedBefore}T00:00:00Z"

    for token in to_retrieve:
        # if base url has not been requested yet, request base url

        if token == "":
            r = requests.get(url['search'], params=search_params)
        else:
            search_params['pageToken'] = token
            r = requests.get(url['search'], params=search_params)

        units += quota_cost['search']
        logger.info(f'Getting requests {r.url}. {units}/{max_quota} used.')

        r.raise_for_status()

        if r.status_code == 403:
            print(r.json()['error']['message'])
            break

        # get nextPageToken from current response and insert it to the database
        try:
            next_page_token = r.json()['nextPageToken']
            db.execute(
                "insert or ignore into search_api_response(next_page_token) values (?)", (next_page_token,))
        except KeyError as e:
            print(f"{e}. No more page to paginate...")

        # update database with response from current request
        with db:
            db.execute(
                """
                replace into search_api_response(next_page_token,
                                                   request_url,
                                                   status_code,
                                                   response,
                                                   total_results,
                                                   retrieval_time)
                values (?,?,?,?,?,?)
                """,
                (token, r.url, r.status_code, json.dumps(r.json()), len(r.json()['items']),
                 datetime.utcnow())
            )

        # update quota usage
        with quota_db:
            quota_db.execute("replace into quota(id, quota, timestamp) values (?,?,?)",
                             (0, units, datetime.now(tz=tz.UTC)))

        time.sleep(random.uniform(3, 6))

# STEP 2. PROCESS SEARCH RESULTS DATA INTO DATABASE
# another function
logger.info("Processing search results responses.")
logger.info("Creating search_results schema.")
with db:
    db.execute(
        """
        create table if not exists search_results(
             /*
            This table stores the processed data from Youtube API responses
            */
             video_id primary key,
             published_at,
             channel_id,
             title,
             description,
             channel_title
         );
        """)
    search_api_responses = db.execute(
        "select response from search_api_response where response notnull")

logger.info("Extracting data from json.")

for row in search_api_responses:
    items = json.loads(row[0])['items']

    for item in items:
        video_id = item['id']['videoId']
        published_at = item['snippet']['publishedAt']
        channel_id = item['snippet']['channelId']
        title = html.unescape(item['snippet']['title'])
        description = item['snippet']['description']
        channel_title = item['snippet']['channelTitle']

        with db:
            db.execute("""
                            insert or ignore into search_results(video_id,
                                                                published_at,
                                                                channel_id,
                                                                title,
                                                                description,
                                                                channel_title) values (?,?,?,?,?,?)
                            """,
                       (video_id, published_at, channel_id,
                        title, description, channel_title)
                       )

        del video_id, published_at, channel_id, title, description, channel_title

    del item, items

logger.info("Data processing complete.")

# STEP 3: ENRICH RESULTS DATASET WITH VIDEO INFORMATION, IF SPECIFIED
# YouTube API accepts a list of up to 50 video ids, so this script makes several requests, each searching for 50 videos
# one function
# break helper function to get vid ids from search data

# create all the tables in one function
if args.video:

    logger.info("Getting video data...")

    logger.info("Creating video_api_response schema.")

    db.executescript(
        """
        create table if not exists video_api_response(
                /*
                This table records the requests made to Youtube API Video endpoint.
                Each row represents a URL of the request made.

                If a request has not been made, it won't be in this database.
                */
                video_id primary key,
                response,
                retrieval_time
                );

        insert or ignore into video_api_response(video_id) select distinct video_id from search_results;
        """)

    while True:

        units, quota_last_time = check_quota(quota_db)

        handle_limit(units=units, max_quota=max_quota,
                     quota_last_time=quota_last_time)

        logger.info("Extracting uncaptured video_ids from database...")

        vid_ids = [row[0]
                   for row in
                   db.execute("select video_id from video_api_response where retrieval_time is null limit 50")]

        if vid_ids:

            video_params = {
                'part': 'snippet,statistics,topicDetails,status',
                'id': ','.join(vid_ids),
                'maxResults': 50,
                'fields': "nextPageToken,prevPageToken,items(id,snippet(publishedAt,channelId,title,description,"
                          "channelTitle),status(uploadStatus),statistics,topicDetails)",
                'key': os.environ['YOUTUBE_API_KEY']
            }

            response = requests.get(url['video'], params=video_params)
            response.raise_for_status()

            logging.info(
                f"Getting data from Youtube Video API... {units}/{max_quota} used.")
            units += quota_cost['video']

            logger.info("Inserting data to video_api_response")

            with db:
                for i, video in enumerate(response.json()['items']):
                    video_id = video['id']
                    logger.info(
                        f"Inserting {video_id}. {i + 1}/{len(response.json()['items'])}...")
                    db.execute(
                        "replace into video_api_response(video_id, response, retrieval_time) values (?,?,?)",
                        (video_id, json.dumps(video), datetime.utcnow())
                    )

            del response

            # update quota usage
            with quota_db:
                quota_db.execute("replace into quota(id, quota, timestamp) values (?,?,?)",
                                 (0, units, datetime.now(tz=tz.UTC)))

            sleep = random.uniform(3, 6)
            time.sleep(sleep)

        else:
            logger.info("No more videos to query.")
            break

    # 3a. Processing video responses

    logging.info(f"Processing video responses...")
    logger.info("Creating `videos` schema.")

    with db:
        db.execute(
            """
            create table if not exists videos(
                 /*
                This table stores the processed data from Youtube API responses
                */
                 video_id primary key,
                 published_at,
                 channel_id,
                 title,
                 description,
                 channel_title,
                 topic_categories,
                 upload_status,
                 view_count,
                 like_count,
                 comment_count
             );
            """)
        video_api_responses = list(
            db.execute("select video_id, response from video_api_response where response notnull"))

    for i, row in enumerate(video_api_responses):

        logging.info(f"Processing item {i + 1}/{len(video_api_responses)}.")

        video_id = row[0]
        item = json.loads(row[1])

        published_at = item['snippet']['publishedAt']
        channel_id = item['snippet']['channelId']
        title = item['snippet']['title']
        description = item['snippet']['description']
        channel_title = item['snippet']['channelTitle']

        if item.get('topicDetails'):
            topic_categories = item['topicDetails'].get('topicCategories')
        else:
            topic_categories = None

        if item.get('status'):
            upload_status = item['status'].get('uploadStatus')
        else:
            upload_status = None

        if item.get('statistics'):
            view_count = item['statistics'].get('viewCount')
            like_count = item['statistics'].get('likeCount')
            comment_count = item['statistics'].get('commentCount')

        with db:
            db.execute(
                """
                insert or replace into videos values (?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    video_id, published_at, channel_id, title, description, channel_title, str(
                        topic_categories),
                    upload_status,
                    view_count, like_count, comment_count))

        del item

    logging.info("Finished processing video data.")

# STEP 4: ENRICH RESULTS DATASET WITH CHANNEL INFORMATION, IF SPECIFIED.
# YouTube API accepts a list of up to 50
# channel ids, so this script makes several requests, each searching for 50 channels

if args.channel:

    logger.info("Getting channel data...")

    logger.info("Creating channel_api_response schema.")

    db.executescript(
        """
        create table if not exists channel_api_response(
                /*
                This table records the requests made to Youtube API Channel endpoint.
                Each row represents a URL of the request made.

                If a request has not been made, it won't be in this database.
                */
                channel_id primary key,
                response,
                retrieval_time
                );

        insert or ignore into channel_api_response(channel_id) select distinct channel_id from search_results;
        """)

    while True:

        units, quota_last_time = check_quota(quota_db)

        handle_limit(units=units, max_quota=max_quota,
                     quota_last_time=quota_last_time)

        logger.info("Extracting uncaptured channel_ids from database...")

        chnl_ids = [row[0]
                    for row in
                    db.execute("select channel_id from channel_api_response where retrieval_time is null limit 50")]

        if chnl_ids:

            channel_params = {
                'part': 'snippet,statistics,topicDetails,status',
                'id': ','.join(chnl_ids),
                'maxResults': 50,
                'fields': "nextPageToken,prevPageToken,items(id,snippet(publishedAt,title,description"
                          "),status,statistics,topicDetails)",
                'key': os.environ['YOUTUBE_API_KEY']
            }

            response = requests.get(url['channel'], params=channel_params)
            response.raise_for_status()

            logging.info(f"Getting {response.url}")
            logging.info(
                f"Getting data from Youtube Channel API... {units}/{max_quota} used.")
            units += quota_cost['channel']

            logger.info("Inserting data to channel_api_response")

            with db:
                try:
                    for i, channel in enumerate(response.json()['items']):
                        channel_id = channel['id']
                        logger.info(
                            f"Inserting {channel_id}. {i + 1}/{len(response.json()['items'])}...")
                        db.execute(
                            "replace into channel_api_response(channel_id, response, retrieval_time) values (?,?,?)",
                            (channel_id, json.dumps(channel), datetime.utcnow())
                        )
                except KeyError:
                    logging.info(f"No items found for {response.url}.")
                    for chnl_id in chnl_ids:
                        db.execute(
                            "replace into channel_api_response(channel_id, retrieval_time) values (?,?)",
                            (chnl_id, datetime.utcnow())
                        )

            del response

            # update quota usage
            with quota_db:
                quota_db.execute("replace into quota(id, quota, timestamp) values (?,?,?)",
                                 (0, units, datetime.now(tz=tz.UTC)))

            sleep = random.uniform(3, 6)
            time.sleep(sleep)

        else:
            logger.info("No more channels to query.")
            break

    # 4a. Processing channel responses

    logging.info("Processing channel responses...")
    logger.info("Creating `channels` schema.")

    with db:
        db.execute(
            """
            create table if not exists channels(
                 /*
                This table stores the processed data from Youtube API responses
                */
                 channel_id primary key,
                 ch_published_at,
                 ch_title,
                 ch_description,
                 ch_topic_categories,
                 ch_view_count,
                 ch_subscriber_count,
                 ch_video_count
             );
            """)
        channel_api_responses = list(db.execute(
            """
                                    select channel_id, response from channel_api_response where response notnull
                                    """))

    for i, row in enumerate(channel_api_responses):

        logging.info(f"Processing item {i + 1}/{len(channel_api_responses)}.")

        channel_id = row[0]
        item = json.loads(row[1])

        ch_published_at = item['snippet']['publishedAt']
        ch_title = item['snippet']['title']
        ch_description = item['snippet']['description']
        ch_title = item['snippet']['title']

        if item.get('topicDetails'):
            ch_topic_categories = item['topicDetails'].get('topicCategories')
        else:
            ch_topic_categories = None

        if item.get('statistics'):
            ch_view_count = item['statistics'].get('viewCount')
            ch_subscriber_count = item['statistics'].get('subscriberCount')
            ch_video_count = item['statistics'].get('videoCount')

        with db:
            db.execute(
                """
                insert or replace into channels values (?,?,?,?,?,?,?,?)
                """,
                (channel_id, ch_published_at, ch_title, ch_description, str(ch_topic_categories),
                 ch_view_count, ch_subscriber_count, ch_video_count))

    logging.info("Finished processing video data.")

# STEP 6. Combine everything together and export to csv

# another module but probs not confined to csv
if args.to_csv:
    logging.info("Exporting data...")

    full_data = db.execute(
        """
        select video_id, published_at, title, description, topic_categories, upload_status, view_count, like_count, comment_count,
        channel_title, videos.channel_id, ch_published_at, ch_description, ch_topic_categories, ch_view_count, ch_subscriber_count, ch_video_count
        from videos
        left join channels
        on videos.channel_id = channels.channel_id;
        """
    )

    headers = ["video_id", "published_at", "title", "description", "topic_categories", "upload_status", "view_count",
               "like_count", "comment_count",
               "channel_title", "channel_id", "ch_published_at", "ch_description", "ch_topic_categories",
               "ch_view_count",
               "ch_subscriber_count", "ch_video_count"]

    with open(f'{dbpath[:-3]}.csv', 'w', newline='', encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)
        writer.writerows(full_data)
