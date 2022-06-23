# youtupy

A command line utility to get Youtube video metadata from Youtube API.

Requires Youtube API Key to be put in a YOUTUBE_API_KEY environment variable. For DO, use the staging API key for testing (stored in 1password).

## Installation

(for testing purpose only)

```shell
git clone git@github.com:QUT-Digital-Observatory/youtupy.git
cd youtupy

# create a virtual environment (Linux)
python3 -m venv venv
source venv/bin/activate

# other any other ways of creating virtual environments

# install package (note the dot "." at the end)
pip install -e .
```

## Run a search

```
youtupy collect --query <search query> --start <YYYY-MM-DD> --end <YYYY-MM-DD> --video --channel <destination database.db> --max-quota 10000
```

- The default settings is to run a search via Youtube's Search endpoint.
- The `--video` and `--channel` flags specify whether additional video and channel information are retrieved, using the Video and Channel endpoints.
- Raw responses are stored in one to three tables in the destination database:
  - search_api_response
  - video_api_response (if `--video` is specified)
  - channel_api_response (if `--channel` is specified)
- At the moment, one database can only contain one collection (same search query, start date and end date arguments).
- The default maximum quota is 10,000, assuming usage of the free version of Youtube API. If quota is exceeded, the script will wait until quota reset time (midnight Pacific Time) before resuming.
  - You can change the maximum quota by adding a `--max-quota` option.

## Process data

```
youtupy process <database.db>
```

- Process raw responses from database and store clean data in one to three tables in the same database:
  - search_results
  - videos
  - channels

### Data schema:

1. `videos` table:
- video_id
- published_at
- channel_id
- title
- description
- channel_title
- topic_categories
- upload_status
- view_count: will be `NULL` if the view stats is disabled/set private for the video
- like_count: will be `NULL` if the like stats is disabled/set private for the video
- comment_count: will be `NULL` if commenting is disabled for the video

2. `channels` table:
- channel_id
- ch_published_at
- ch_title
- ch_description
- ch_topic_categories
- ch_view_count: will be `NULL` if the view stats is disabled/set private for the channel
- ch_subscriber_count: will be `NULL` if the like stats is disabled/set private for the channel
- ch_video_count: will be `NULL` if the video stats is disabled/set private for the channel

## About YouTube quota

Free accounts get a API quota cap of 10,000 units per day, which resets at midnight Pacific Time. Each endpoint will have a different usage cost. Right now, a *search* call will cost 100 units, whereas a `video` or `channel` call will cost 1 unit.

While you can check how many units you've used in Google Cloud Console, there is no way to monitor API usage within a script. So manual workaround is needed.

Quota data is stored in an SQLite database in a **.quota** folder in your current directory.
