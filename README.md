# youtupy

A command line utility to get Youtube video metadata from Youtube API.

Requires Youtube API Key to be put in a YOUTUBE_API_KEY environment variable. For DO, use the staging API key for testing.

## Run a search

```
youtupy collect --query <search query> --start <YYYY-MM-DD> --end <YYYY-MM-DD> --video --channel <destination database.db>
```

- The default settings is to run a search via Youtube's Search endpoint.
- The `--video` and `--channel` flags specify whether additional video and channel information are retrieved, using the Video and Channel endpoints.
- Raw responses are stored in one to three tables in the destination database:
  - search_api_response
  - video_api_response (if `--video` is specified)
  - channel_api_response (if `--channel` is specified)
- At the moment, one database can only contain one collection (same search query, start date and end date arguments).
- The default maximum quota is 10,000, assuming usage of the free version of Youtube API.

## Process data

```
youtupy process <database.db>
```

- Process raw responses from database and store clean data in one to three tables in the same database:
  - search_results
  - videos
  - channels
