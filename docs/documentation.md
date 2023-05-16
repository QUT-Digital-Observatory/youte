---
title: "youte documentation"
---

## Changes from youte 1.3.0

Several major changes are made in youte 2.x. To better correspond with YouTube API endpoints and avoid confusion:

- `youte hydrate` is now broken down to `youte videos` and `youte channels`, 
- `youte get-comments` is now `youte comments` and `youte replies`.
- `youte most-popular` is now `youte chart`
- `youte get-related` is now `youte related-to`

Furthermore:

- Resuming searches is no longer available. Instead, you can set a limit on the number of search pages returned to avoid exhausting your API quota.
- All youte commands that retrieve data from YouTube API now won't print results to the shell, but store them in a specified json or jsonl file. This is to avoid clogging up the shell.

## Terminology

An understanding of how YouTube API refers to things can help you make the most out of youte. All entities that make up the YouTube experience are called **resources**. A resource can be a video, a channel, a comment, or a reply to a comment. These are the _types_ of a resource.

Each resource has its own unique identifier, or ID, assigned and provided by YouTube. The IDs can be seen within the browser for some resource types, such as videos and comments. For others, such as channels, a more reliable way to get their IDs would be from results returned from the API using youte. Many of YouTube API endpoints work with resource IDs. Hence, these IDs are very useful. youte has functionalities that support operating with resource IDs.

## Code convention in this documentation

Anything within pointy brackets (`<>`) is for the users to input. Do not include the brackets when running `youte`.

## Installation

```shell
python -m pip install youte
```

## YouTube API key

To get data from YouTube API, you will need a YouTube API key. Follow YouTube [instructions](https://developers.google.com/youtube/v3/getting-started) to obtain a YouTube API key if you do not already have one.

## config

### Store your API key

While API key can be passed straight to youte commands, you can save your API key in a youte config file for reuse. To do so, run:

```shell
youte config add-key
```

In the interactive prompt, enter your API key and give it a name. The name is used to identify the key and can be anything you choose.

You can also choose to set the key as default. When running queries, if no API key or name is specified, `youte` will automatically use the default key.

### See the list of all keys

To see the list of all keys and their names that have been stored in the config, run:

```shell
youte config list-keys
```

The default key, if there is one, will have an asterisk next to it.

### Manually set a key as default

If you want to manually set an existing key as a default, run:

```shell
youte config set-default <name-of-existing-key>
```

Note that what is passed to this command is the _name_ of the API key, not the API key itself. The API key has to be first added to the config file using `youte config add-key`. If you use a name that has not been added to the config file, an error will be raised.

### Remove a key

To remove a stored key, run:

```shell
youte config remove <name-of-key>
```

### About the config file

youte's config file is stored in a central place whose exact location depends on the running operating system:

- Linux/Unix: ~/.config/youte/
- Mac OS X: ~/Library/Application Support/youte/
- Windows: C:\Users\\\<user>\\AppData\\Roaming\\youte

## search

Searching can be as simple as:

```bash
youte search <search-terms> --key <API-key> --outfile <name-of-file.json>
# OR
youte search <search-terms> --key <API-key> -o <name-of-file.json>
```

If you have a default key set up using `youte config`, then there is no need to specify an API key using `--key`.

This will return the maximum number of results pages (around 12-13) matching the search terms and store them in a JSON file. Unlike version 1.3, youte 2.0 does not print results to the terminal to avoid clogging it up. Instead, `--outfile` is now a required option.

In the search terms, you can also use the Boolean NOT (-) and OR (|) operators to exclude videos or to find videos that match one of several search terms. If the terms contain spaces, the entire search term value has to be wrapped in quotes.

Prettify JSON results by using the flag `--pretty`:

```bash
youte search <search-terms> --key <API-key> --outfile <name-of-file> --pretty
```

### Limit pages returned

Searching is very expensive in terms of API usage - a single results page uses up 100 points - 1% of your standard daily quota. Therefore, you can limit the maximum number of result pages returned, so that a search doesn't go on and exhaust your API quota.

```bash
youte search <search-terms> --max-pages 5
# OR
youte search <search-terms> -m 5
```

### Tidy data

Raw JSONs from YouTube API contain query metadata and nested fields. You can tidy these data into a CSV or a flat JSON using `--tidy-to`. The default format that youte will tidy data into will be CSV.

```bash
youte search <search-terms> --tidy-to <file.csv>
```

Specify `--format json` if you want to tidy raw data into an array of flat JSON objects.

```bash
youte search <search-terms> --tidy-to <file-name.json> --format json
```

`--tidy-to` option is available for and works the same across all `youte` commands that retrieve data.

### Advanced search

There are multiple filters to refine your search. A full list of these are provided below:

``` {.bash .no-copy}
Options:
  --type TEXT                     Type of resource to search for  [default:
                                  video]
  --order [date|rating|relevance|title|videoCount|viewCount]
                                  Sort results  [default: date]
  --safe-search [none|moderate|strict]
                                  Include or exclude restricted content
                                  [default: none]
  --lang TEXT                     Return results most relevant to a language
                                  (ISO 639-1 two-letter code)
  --region TEXT                   Return videos viewable in the specified
                                  country (ISO 3166-1 alpha-2 code)  [default:
                                  US]
  --video-duration [any|long|medium|short]
                                  Include videos of a certain duration
  --channel-type [any|show]       Restrict search to a particular type of
                                  channel
  --video-type [any|episode|movie]
                                  Search a particular type of videos
  --caption [any|closedCaption|none]
                                  Filter videos based on if they have captions
  --definition, --video-definition [any|high|standard]
                                  Include videos by definition
  --dimension, --video-dimension [any|2d|3d]
                                  Search 2D or 3D videos
  --embeddable, --video-embeddable [any|true]
                                  Search only embeddable videos
  --license, --video-license [any|creativeCommon|youtube]
                                  Include videos with a certain license
  --location FLOAT...             Lat and long coordinates to restrict search
                                  to. --radius must be specified
  --radius TEXT                   Define the geographic area to restrict
                                  search. Must be a number with a unit
```

#### Restrict by date range

The `--from` and `--to` options allow you to restrict your search to a specific period. The input values have to be in ISO format (YYYY-MM-DD). Currently, all dates and times in youte are in Coordinated Universal Time (UTC). 

#### Restrict by type

The `--type` option specifies the type of results returned, which by default is videos. The accepted values are `channel`, `playlist`, `video`, or a combination of these three. If more than one type is specified, separate each by a comma.

```shell
youte search <search-terms> --limit 5 --type playlist,video
```

#### Restrict by language and region

The `--lang` returns results most relevant to a language. Not all results will be in the specified language: results in other languages will still be returned if they are highly relevant to the search query term. To specify the language, use [ISO 639-1 two letter code](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes), except that you should use the values `zh-Hans` for simplified Chinese and `zh-Hant` for traditional Chinese.

The `--region` returns results viewable in a region. It does *not* filter videos uploaded in that region only. To specify the region, use [ISO 3166-1 alpha-2 country code](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2).

The `--location` and `--radius` options define a circular geographic area to filter videos that specify, in their metadata, a location within this area. This is *not* a robust and reliable way to geolocate YouTube videos and hence should be used with care.

-  `--location` takes in 2 values - the latitude/longitude coordinates that represent the centre of the area. Separate the 2 values with a comma.
-  `--radius` specifies the maximum distance that the location associated with a video can be from that point for the video to still be included in the search results. It must be a number followed by a unit. Valid units are `m`, `km`, `ft`, and `mi`. For example, `1500m`, `5km`, `10000ft`, and `0.75mi`.

Both `--location` and `--radius` have to be specified if they are to be used, otherwise an API error will be thrown.

### Sort results

The `--order` option specifies how results will be sorted. The following values are accepted:

- `date`: Resources are sorted in reverse chronological order based on the date they were created (default value).
- `rating`: Resources are sorted from highest to lowest rating.
- `relevance`: Resources are sorted based on their relevance to the search query.
- `title` – Resources are sorted alphabetically by title.
- `videoCount` – Channels are sorted in descending order of their number of uploaded videos.
- `viewCount` – Resources are sorted from highest to lowest number of views. For live broadcasts, videos are sorted by number of concurrent viewers while the broadcasts are ongoing.

## videos

`youte videos` takes in one or multiple video IDs and retrieve all public metadata for those videos. This is useful in complementing results returned from `youte search`, as what you get from `youte search` only contains a limited amount of information.

```shell
youte videos <video-id>.... -o <file.json>
```

You can put as many IDs as you need, separating each with a space.

As with `youte search`, you can also tidy the data to a CSV using the `--tidy-to` option.

```shell
youte videos <video-id>.... -o <file.json> --tidy-to <file-name.csv>
```

### Use IDs from text file

You can hydrate a list of video ids stored in a text file by using `--file-path` or `-f`. The text file should contain a line-separated list of video ids, with no header.

```shell
youte videos -f <id-file.csv> -o <file.json>
```

This option is often used in combination with `youte dehydrate`, which retrieves the ids from results returned by `youte search` and stores them in a text file.

## channels

`youte channels` works the same as `youte videos`, except it retrieves channel metadata from channel ids.

## comments

`youte comments` retrieves top-level comments (comment threads) on videos or channels. It takes in a list of video or channel ids, followed by a flag indicating the type of these ids (i.e. videos or channels). Only one type of ids should be specified.

To retrieve comments on videos, specify the video ids and pass the `--by-video-id` or `-v` flag.

```shell
youte comments <id>... --by-video-id --outfile <file.json>
# OR
youte comments <id>... -v --outfile <file.json>
```

To retrieve comments on channels, specify channel ids and pass the `--by-channel-id` or `-c` flag.

```shell
youte comments <id>... --by-channel-id --outfile <file.json>
# OR
youte comments <id>... -c --outfile <file.json>
```

If neither of the flags are specified, `youte comments` will assume the ids are thread ids and retrieve the full metadata for those threads.

You can search within the threads and filter threads matching the search terms, by using the `--query` or `-q` option.

```shell
youte comments <ids>... -v --outfile <file.json> -q "search term"
```

## replies

While `youte comments` only retrieve top-level comment threads, if those threads have replies, they can be retrieved using `youte replies`. `youte replies` takes a list of thread ids and return the replies to those threads.

```shell
youte replies <ids>... --outfile <file.json>
```

## chart

`youte chart` retrieves the most popular videos in a region, specified by [ISO 3166-1 alpha-2 country codes](https://www.iso.org/obp/ui/#search). If no argument or option is given, it retrieves the most popular videos in the United States.

For example:

```shell
youte chart <region-code> -o <file.json>
```

## related-to

`youte related-to` retrieves a list of videos related to a video.

```shell
youte related-to <video-ids>... -o <file.json>
```

You can pass one or many video IDs. If multiple video IDs are inputted, youte will iterate through those video IDs, retrieving all related videos to each video separately. The end result contains both the related videos and the id of the video that they are related to.

Other options include:

```{.bash .no-copy}
  --safe-search [none|moderate|strict]
                                  Include or exclude restricted content
                                  [default: none]
  --region TEXT                   Specify region the videos can be viewed in
                                  (ISO 3166-1 alpha-2 country code)
  --lang TEXT                     Return results most relevant to a language
                                  (ISO 639-1 two-letter code)
```

## full-archive

A new feature added in `youte` 2.1.0 is the ability to run a full archive workflow in one command. `youte full-archive` runs `youte search`, then retrieving video and channel metadata for the search results, as well as getting comments and replies for those videos as well. All data are then tidied and stored in multiple tables in an SQLite database. 

```shell
youte full-archive <query> [options] -o <name-of-database-file>
```

The search options are identical to `youte search`. Name of the file given to `-o` has to have SQLite extension (i.e. `.db` or `.sqlite`).

Below are the list of tables and the corresponding YouTube resource that they contain:

- `search_result`: search results from `youte search`
- `video`: videos
- `channel`: channels
- `commment`: comment threads and replies

Warning: since `full-archive` will potentially run a large number of queries, it's important to ensure that you have enough API quota. You can select which resources to retrieve by using the `--select` option. `--select` takes one or a comma-separated list of YouTube resource types, namely `video`, `channel`, `thread`, and `reply`.

Note that if you select `reply`, `thread` also has to be selected. This is because comment thread replies are retrieved using thread IDs, thus collecting comment threads is a must before collecting the replies. Because of that, if you want to archive the replies, both 'thread' and 'reply' will have to be specified.

## dehydrate

`dehydrate` extracts the IDs from a JSON file returned from YouTube API.

```shell
youte dehydrate <file-name.json>
```

```{.shell .no-copy}
Options:
  -o, --output FILENAME  Output text file to store IDs in
```

## Debugging

The `--verbosity` option, available for most `youte` commands, allows you to turn on debugging messages of the program. Simply specify `--verbosity DEBUG` to turn this mode on.

## Metadata

By default, youte includes, for data provenance, some metadata in the returned output of all query commands. All metadata is accessible via the `_youte` field in the JSON object. Default metadata includes the youte version, data collection timestamp, the operating system, and python version.

You can turn this feature off and choose not to include metadata by specifying `--no-metadata`. For example:

```shell
youte search "aukus" -o aukus.json --no-metadata
```

## Using youte as a Python module

### `Youte` class

Alternatively, you can also incorporate `youte` in a Python script. The first thing to do is creating an instance of the `Youte` class. The only argument needed for this step is your API key.

```python linenums="1" title="youtube.py"
import os
from youte.collector import Youte

# suppose the API key is stored in an 
# environment variable named YOUTUBE_API_KEY
yob = Youte(api_key=os.environ["YOUTUBE_API_KEY"])
```

Instances of `Youte` class have a number of methods to query data from YouTube Data API:

- `search()`
- `get_channel_metadata()`
- `get_video_metadata()`
- `get_comment_threads()`
- `get_thread_replies()`
- `get_related_videos()`
- `get_most_popular()`

Refer to the [API documentation](reference.md#youte.collector.Youte) for more details on the arguments of each method. All of these methods return a generator of Python dictionaries that you can iterate over.

For example, to run a YouTube search, run the `search()` method. 

```python linenums="8" title="youtube.py"
results = yob.search(
    query="aukus", 
    order="date", 
    caption="closedCaption", 
    max_pages_retrieved=2
)
for r in results:
    print(r)
```

```pycon
{'kind': 'youtube#searchListResponse', 'etag': 'BCJ3FrFh-mOwfoQ6XsF74z7rL60', 'nextPageToken': 'CAoQAA', 'regionCode': 'AU', 'pageInfo': {'totalResults': 135036, 'resultsPerPage': 10}, 'items': [{'kind': 'youtube#searchResult', 'etag': 'oeJugkxLr13mjtwAyDWjHjsWNkA', 'id': {'kind': 'youtube#video', 'videoId': '4PA9HLMIeKU'}, 'snippet': {'publishedAt': '2023-04-10T18:19:31Z', 'channelId': 'UCjD1X7Cv1N01_tQVj54Hqng', 'title': 'Exclusive Insight: From AUKUS Fallout to Ukraine Stalemate I China Brief (20230410)', 'description': '六度世界store front 链接： ...', 'thumbnails': {'default': {'url': 'https://i.ytimg.com/vi/4PA9HLMIeKU/default.jpg', 'width': 120, 'height': 90}, 'medium': {'url': 'https://i.ytimg.com/vi/4PA9HLMIeKU/mqdefault.jpg', 'width': 320, 'height': 180}, 'high': {'url': 'https://i.ytimg.com/vi/4PA9HLMIeKU/hqdefault.jpg', 'width': 480, 'height': 360}}, 'channelTitle': 'The China Briefing', 'liveBroadcastContent': 'none', 'publishTime': '2023-04-10T18:19:31Z'}}, {'kind': 'youtube#searchResult', 'etag': 'VyXpSosupcamPneu3HXdQjC2oq8', 'id': {'kind': 'youtube#video', 'videoId': '4yEzoj_ko10'}, 'snippet': {'publishedAt': '2023-04-07T02:00:01Z', 'channelId': 'UCTBHlrCFWHLt4ux0UChYRSw', 'title': 'TNI MINTA AUKUS JANGAN BERDAMPAK KE INDONESIA', 'description': 'berita terbaru militer Indonesia dan ASEAN. Indonesia minta supaya kesepakatan AUKUS tidak mengganggu Indonesia.', 'thumbnails': {'default': {'url': 'https://i.ytimg.com/vi/4yEzoj_ko10/default.jpg', 'width': 120, 'height': 90}, 'medium': {'url': 'https://i.ytimg.com/vi/4yEzoj_ko10/mqdefault.jpg', 'width': 320, 'height': 180}, 'high': {'url': 'https://i.ytimg.com/vi/4yEzoj_ko10/hqdefault.jpg', 'width': 480, 'height': 360}}, 'channelTitle': 'Banyak Cakap', 'liveBroadcastContent': 'none', 'publishTime': '2023-04-07T02:00:01Z'}}, {'kind': 'youtube#searchResult', 'etag': 'oReYIYZDWOPec-32cEs1WTfvrk4', 'id': {'kind': 'youtube#video', 'videoId': '79qIf46nkxY'}, 'snippet': {'publishedAt': '2023-04-04T11:00:11Z', 'channelId': 'UCI4Habp7f589LUxFTGNK4Kg', 'title': '2450億美金！史上最大軍事合作專案AUKUS敲定，澳大利亞海軍未來核潛艇數量將達到僅次於英美俄的全球第四！', 'description': '2023年3月13日，美國總統拜登、英國首相蘇納克和澳大利亞總理阿爾巴尼斯在美國聖迭戈海軍基地會面，英美澳三方就奧庫 ...', 'thumbnails': {'default': {'url': 'https://i.ytimg.com/vi/79qIf46nkxY/default.jpg', 'width': 120, 'height': 90}, 'medium': {'url': 'https://i.ytimg.com/vi/79qIf46nkxY/mqdefault.jpg', 'width': 320, 'height': 180}, 'high': {'url': 'https://i.ytimg.com/vi/79qIf46nkxY/hqdefault.jpg', 'width': 480, 'height': 360}}, 'channelTitle': '火力就是正義（百科頻道）', 'liveBroadcastContent': 'none', 'publishTime': '2023-04-04T11:00:11Z'}}, {'kind': 'youtube#searchResult', 'etag': 'sA_y_q_lAbW3VWidWPWzj4qLCrk', 'id': {'kind': 'youtube#video', 'videoId': 'hbh6fsxGq4Y'}, 'snippet': {'publishedAt': '2023-03-25T04:27:24Z', 'channelId': 'UCnyfVAHIgv8DpioA-_g_gAA', 'title': 'Why Aukus Is a Game-Changer for International Security | USA News| 12am বাংলা', 'description': "Why Aukus Is a Game-Changer for International Security | USA News| 12am Bangla Meeting of countries' leaders comes 18 ...", 'thumbnails': {'default': {'url': 'https://i.ytimg.com/vi/hbh6fsxGq4Y/default.jpg', 'width': 120, 'height': 90}, 'medium': {'url': 'https://i.ytimg.com/vi/hbh6fsxGq4Y/mqdefault.jpg', 'width': 320, 'height': 180}, 'high': {'url': 'https://i.ytimg.com/vi/hbh6fsxGq4Y/hqdefault.jpg', 'width': 480, 'height': 360}}, 'channelTitle': '12am বাংলা', 'liveBroadcastContent': 'none', 'publishTime': '2023-03-25T04:27:24Z'}}, {'kind': 'youtube#searchResult', 'etag': 'uJFRL7FGN0-UmsVQ_AejOnWyBfo', 'id': {'kind': 'youtube#video', 'videoId': 'LUSxgWiExDQ'}, 'snippet': {'publishedAt': '2023-03-24T21:02:37Z', 'channelId': 'UC9BRnPnCn1L-sDS4OdqJx4Q', 'title': 'AUKUS, The Voice, anti-trans Nazis trouble and election time in NSW', 'description': 'In this episode: the week in federal politics; the AUKUS deal; the Voice to Parliament; and the safeguard mechanism for emissions ...', 'thumbnails': {'default': {'url': 'https://i.ytimg.com/vi/LUSxgWiExDQ/default.jpg', 'width': 120, 'height': 90}, 'medium': {'url': 'https://i.ytimg.com/vi/LUSxgWiExDQ/mqdefault.jpg', 'width': 320, 'height': 180}, 'high': {'url': 'https://i.ytimg.com/vi/LUSxgWiExDQ/hqdefault.jpg', 'width': 480, 'height': 360}}, 'channelTitle': 'New Politics', 'liveBroadcastContent': 'none', 'publishTime': '2023-03-24T21:02:37Z'}}, {'kind': 'youtube#searchResult', 'etag': 'kCoPb2dly6ZdL3X0tOkyszs-LZM', 'id': {'kind': 'youtube#video', 'videoId': 'WMfzmSncPW8'}, 'snippet': {'publishedAt': '2023-03-24T11:14:47Z', 'channelId': 'UC9BRnPnCn1L-sDS4OdqJx4Q', 'title': 'PREVIEW: AUKUS and the Voice, anti-trans Nazis trouble and the NSW election', 'description': 'In this episode: we look at the week in federal politics, including the AUKUS deal; the Voice to Parliament; and the safeguard ...', 'thumbnails': {'default': {'url': 'https://i.ytimg.com/vi/WMfzmSncPW8/default.jpg', 'width': 120, 'height': 90}, 'medium': {'url': 'https://i.ytimg.com/vi/WMfzmSncPW8/mqdefault.jpg', 'width': 320, 'height': 180}, 'high': {'url': 'https://i.ytimg.com/vi/WMfzmSncPW8/hqdefault.jpg', 'width': 480, 'height': 360}}, 'channelTitle': 'New Politics', 'liveBroadcastContent': 'none', 'publishTime': '2023-03-24T11:14:47Z'}}, {'kind': 'youtube#searchResult', 'etag': 'D4iA8OGdny5WBuMQriovY5e3G9Y', 'id': {'kind': 'youtube#video', 'videoId': 'JCB2fyPlXNU'}, 'snippet': {'publishedAt': '2023-03-22T23:28:31Z', 'channelId': 'UCffCl3lHcLRI9vaMTFVc0zg', 'title': 'AUKUS DEAL MATTER OF INTEREST', 'description': '', 'thumbnails': {'default': {'url': 'https://i.ytimg.com/vi/JCB2fyPlXNU/default.jpg', 'width': 120, 'height': 90}, 'medium': {'url': 'https://i.ytimg.com/vi/JCB2fyPlXNU/mqdefault.jpg', 'width': 320, 'height': 180}, 'high': {'url': 'https://i.ytimg.com/vi/JCB2fyPlXNU/hqdefault.jpg', 'width': 480, 'height': 360}}, 'channelTitle': 'GreensMPsSA', 'liveBroadcastContent': 'none', 'publishTime': '2023-03-22T23:28:31Z'}}, {'kind': 'youtube#searchResult', 'etag': 'cXuAGmDgzRuQqzOsY_j95qpDwqw', 'id': {'kind': 'youtube#video', 'videoId': 'aL295tjyFBo'}, 'snippet': {'publishedAt': '2023-03-22T09:34:48Z', 'channelId': 'UC3dEet-HxoTy4dObGrfqIvg', 'title': 'Indonesia Komentari Pakta Kapal Selam Nuklir AUKUS, Minta Australia Patuh Non-proliferasi#indonesia', 'description': 'Indonesia Komentari Pakta Kapal Selam Nuklir AUKUS, Minta Australia Patuh Non-proliferasi Indonesia sudah mendesak ...', 'thumbnails': {'default': {'url': 'https://i.ytimg.com/vi/aL295tjyFBo/default.jpg', 'width': 120, 'height': 90}, 'medium': {'url': 'https://i.ytimg.com/vi/aL295tjyFBo/mqdefault.jpg', 'width': 320, 'height': 180}, 'high': {'url': 'https://i.ytimg.com/vi/aL295tjyFBo/hqdefault.jpg', 'width': 480, 'height': 360}}, 'channelTitle': 'KATANIKA', 'liveBroadcastContent': 'none', 'publishTime': '2023-03-22T09:34:48Z'}}, {'kind': 'youtube#searchResult', 'etag': 'Z1PXc8TWntH5EDs0Te2jZKD38Ws', 'id': {'kind': 'youtube#video', 'videoId': 'N2an-uPh7OQ'}, 'snippet': {'publishedAt': '2023-03-22T03:41:31Z', 'channelId': 'UCCJO9AnxWyIL3qX7XYzuV1A', 'title': 'Pacific needs to sit up and pay close attention to AUKUS - Dame Meg Taylor :', 'description': 'Pacific needs to sit up and pay close attention to AUKUS - Dame Meg Taylor :', 'thumbnails': {'default': {'url': 'https://i.ytimg.com/vi/N2an-uPh7OQ/default.jpg', 'width': 120, 'height': 90}, 'medium': {'url': 'https://i.ytimg.com/vi/N2an-uPh7OQ/mqdefault.jpg', 'width': 320, 'height': 180}, 'high': {'url': 'https://i.ytimg.com/vi/N2an-uPh7OQ/hqdefault.jpg', 'width': 480, 'height': 360}}, 'channelTitle': '24newsread.blogspot. com', 'liveBroadcastContent': 'none', 'publishTime': '2023-03-22T03:41:31Z'}}, {'kind': 'youtube#searchResult', 'etag': 'CbSwGJuUjOg6DQWOhP35fNLFKHg', 'id': {'kind': 'youtube#video', 'videoId': 'yFzzOM5PAPE'}, 'snippet': {'publishedAt': '2023-03-21T23:46:35Z', 'channelId': 'UCIALMKvObZNtJ6AmdCLP7Lg', 'title': 'China, Russia Express Concerns Over Aukus', 'description': 'China and Russia have expressed serious concerns about the Aukus agreement which will see Australia acquire ...', 'thumbnails': {'default': {'url': 'https://i.ytimg.com/vi/yFzzOM5PAPE/default.jpg', 'width': 120, 'height': 90}, 'medium': {'url': 'https://i.ytimg.com/vi/yFzzOM5PAPE/mqdefault.jpg', 'width': 320, 'height': 180}, 'high': {'url': 'https://i.ytimg.com/vi/yFzzOM5PAPE/hqdefault.jpg', 'width': 480, 'height': 360}}, 'channelTitle': 'Bloomberg Television', 'liveBroadcastContent': 'none', 'publishTime': '2023-03-21T23:46:35Z'}}], 'collection_time': datetime.datetime(2023, 4, 17, 12, 16, 21, 219689)}
```

You can also turn the results into a list for subsequent processing.

```python linenums="16" title="youtube.py"
results = [r for r in 
           yob.search(
               query="aukus", 
               order="date",
               caption="closedCaption",
               max_pages_retrieved=2
           )]
```

The `search()` method comes with a number of options for you to tweak and refine your search. Except `query`, which is a required argument, other options have default values so that you don't have to specify them explicitly but can if you want to. Refer to the [API documentation](reference.md#youte.collector.Youte.search) for more details.

### Parsing

Results returned from the `search()` are standard Python dictionaries, so you can extract the attributes and tidy them as you want. A better way of processing these dictionaries is to use `youte.parser`, which processes these results and returns a Resources object. A Resources object can be a `Searches`, `Videos`, `Channels`, or `Comments` object.

Each resource type has its corresponding parser function. (A potential improvement in the future is to have one all-encompassing parser function that detects resource type and parses data accordingly.) The table below lists out the resulting resource type from each `Youte` methods and its corresponding parser function.

| `Youte` method         | Resulting resource type | Parser function | Object returned from parser function |
|------------------------|-------------------------|-----------------|--------------------------------------|
| search()               | search                  | parse_searches  | `Searches`                           |
| get_video_metadata()   | video                   | parse_videos    | `Videos`                             |
| get_channel_metadata() | channel                 | parse_channels  | `Channels`                           |
| get_comment_threads()  | comment                 | parse_comments  | `Comments`                           |
| get_thread_replies()   | comment                 | parse_comments  | `Comments`                           |
| get_most_popular()     | video                   | parse_videos    | `Videos`                             |
| get_related_videos()   | search                  | parse_searches  | `Searches`                           |

If the wrong parser function is used, a `ValueError` will be raised.

For results from `search()`, we use `parser.parse_searches()`. Simply pass your results from `search()`, either as is or as a list, into `parse_searches()`.

```python linenums="1" title="youtube.py"
from youte.parser import parse_searches

results = [r for r in 
           yob.search(
               query="aukus", 
               order="date",
               caption="closedCaption",
               max_pages_retrieved=2
           )]
searches = parse_searches(results)
type(searches)
```

```pycon
youte.resources.Searches
```

`Searches` object contains a list of `Search` instances which can be accessed via the `.items` attribute. 

```python linenums="12" title="youtube.py"
list_of_searches = searches.items
type(list_of_searches)
print(list_of_searches[0])
```

```pycon
list
[Search(kind='youtube#video', id='4PA9HLMIeKU', published_at=datetime.datetime(2023, 4, 10, 18, 19, 31, tzinfo=datetime.timezone.utc), title='Exclusive Insight: From AUKUS Fallout to Ukraine Stalemate I China Brief (20230410)', description='六度世界store front 链接： ...', channel_id='UCjD1X7Cv1N01_tQVj54Hqng', thumbnail_url='https://i.ytimg.com/vi/4PA9HLMIeKU/hqdefault.jpg', thumbnail_width=480, thumbnail_height=360, channel_title='The China Briefing', live_broadcast_content='none')]
```

Each of the items is a `Search` object, with properties that you can access using the `.` attribute approach. The benefit of parsing raw results into `Search` objects is that all attributes are processed and converted to the correct Python types.

```python linenums="1"
list_of_searches[0].title
```

```pycon
'Exclusive Insight: From AUKUS Fallout to Ukraine Stalemate I China Brief (20230410)'
```

```python linenums="1"
searches.items[0].published_at
```

```pycon
datetime.datetime(2023, 4, 10, 18, 19, 31, tzinfo=datetime.timezone.utc)
```

It's important to note the distinction between the `Searches` class and the `Search` class. 

- A `Search` object is an individual search result entity with attributes that can be accessed via the `.` attribute approach. 
- A `Searches` object contains a list of `Search` objects that can be accessed via the `.items` attribute. It also has some useful methods that will be explained below.

The same distinction applies to other classes (i.e. `Videos` vs. `Video`, `Channels` vs. `Channel`, `Comments` vs. `Comment`).


#### Convert to pandas.DataFrame

`Search` objects are essentially Python dictionaries. Thus, what's in `Searches.items` are essentially a list of Python dictionaries. This makes creating a pandas DataFrame from these fairly simple, using pandas's `DataFrame.from_dict()`.

```python linenums="1"
import pandas as pd

data = pd.DataFrame.from_dict(searches.items)
data.info()
```

```pycon
<class 'pandas.core.frame.DataFrame'>
RangeIndex: 10 entries, 0 to 9
Data columns (total 11 columns):
 #   Column                  Non-Null Count  Dtype              
---  ------                  --------------  -----              
 0   kind                    10 non-null     object             
 1   id                      10 non-null     object             
 2   published_at            10 non-null     datetime64[ns, UTC]
 3   title                   10 non-null     object             
 4   description             10 non-null     object             
 5   channel_id              10 non-null     object             
 6   thumbnail_url           10 non-null     object             
 7   thumbnail_width         10 non-null     int64              
 8   thumbnail_height        10 non-null     int64              
 9   channel_title           10 non-null     object             
 10  live_broadcast_content  10 non-null     object             
dtypes: datetime64[ns, UTC](1), int64(2), object(8)
memory usage: 1008.0+ bytes
```

#### Export to file

##### CSV

You can easily export tidied search results to a CSV file using `Searches.to_csv()` method.

```python linenums="1"
searches.to_csv("search_results.csv")
```

##### JSON

Alternatively, you can export tidied search results as JSON, using the `Searches.to_json()` method.

```python linenums="1"
searches.to_json("search_results.json")
```

### Create a workflow using youte

The `Youte` class and parser functions make up the core toolset that you can use to create a YouTube data collection workflow. 

Let's say we want to collect all the video metadata and comments of videos related to AUKUS. First, we'll have to do a search of videos matching this keyword. Then, we will get the full metadata of the resulting videos, using their IDs. Next, using the same IDs, we will retrieve the comment threads left on videos that have more than 5 comments each. Finally, if those threads have replies, we will retrieve those. Below is an example script for such a workflow.

```python linenums="1" title="aukus_videos.py"
import os
import pandas as pd
from youte import parser
from youte.collector import Youte

yob = Youte(api_key=os.environ["YOUTUBE_API_KEY"])

# Run a search
# For demonstration, let's just get 2 pages of search results back
results = [
    r
    for r in yob.search(
        query="aukus",
        order="date",
        caption="closedCaption",
        max_result=50,
        max_pages_retrieved=2,
        type_="video",
    )
]

# Parse raw data into Searches object
searches = parser.parse_searches(results)

# Extract video ids from search results into a list:
# every Search object in searches.items have an `id` attribute 
video_ids = [s.id for s in searches.items]

# Pass the list of video ids to Youte.get_video_metadata()
# to get full video metadata
results = [r for r in yob.get_video_metadata(video_ids)]

# Parse raw data into Videos object
videos = parser.parse_videos(results)

# Get the list of ids for videos with more than 5 comments:
# every Video object in videos.items have an `comment_count` attribute
videos_with_comments = [v.id for v in videos.items if v.comment_count > 5]
results = [r for r in yob.get_comment_threads(video_ids=videos_with_comments)]

# Parse raw data into Comments object
comments = parser.parse_comments(results)

# Get the id of comment threads with more than 0 replies:
# every Comment object in comments.items have a `total_reply_count` attribute
thread_ids = [t.id for t in comments.items if t.total_reply_count > 0]

# Get the replies to these threads by passing thread ids
# to Youte.get_thread_replies()
results = [r for r in yob.get_thread_replies(thread_ids=thread_ids)]

# Parse raw data into Comments object
replies = parser.parse_comments(results)

# Convert these tidied objects into pandas.DataFrame
search_df = pd.DataFrame.from_dict(searches.items)
video_df = pd.DataFrame.from_dict(videos.items)
comment_df = pd.DataFrame.from_dict(comments.items)
replies_df = pd.DataFrame.from_dict(replies.items)
```

## Troubleshooting

### IDs starting with a dash/hyphen

With IDs starting with a dash (e.g. -Q7G5zfSal8), using the ID in the shell might raise an error, as it might be taken as a command option. For example:

```bash
youte related-to -o related_videos.json -Q7G5zfSal8
```

This command might raise an `Error: No such option: -Q`.

One solution is to escape the dash. In Bash, adding a `--` before will do the trick.

```shell
youte related-to -o related_videos.json -- -Q7G5zfSal8
```

Note that everything after the `--` will be interpreted as raw strings. Thus, you should put all of your options before the `--`. Also note the space between the `--` and the ID.

Alternatively, especially when you have multiple IDs that start with a dash/hyphen, put the IDs in a text file. Refer to [this section](#use-ids-from-text-file) for more details.