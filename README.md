# youte 2.0

A command line utility to get YouTube video metadata and comments from YouTube Data API.

## Changes from youte 1.3.0

Several major changes are made in youte 2.0. To better correspond with YouTube API endpoints and avoid confusion, some commands have been changed.

- `youte hydrate` is now broken down to `youte videos` and `youte channels`.
- `youte get-comments` is now `youte comments` and `youte replies`.
- `youte most-popular` is now `youte chart`.
- `youte get-related` is now `youte related-to`.

Furthermore:

- Resuming search is no longer available. Instead, you can set a limit on the number of search pages returned to avoid exhausting your API quota.
- All youte commands that retrieve data from YouTube API now won't print results to the shell, but store them in a specified json or jsonl file. This is to avoid clogging up the shell.
- You can now tidy data into a CSV or a flat JSON array.

Big thanks to @Lingomat (Mat Bettinson) for code review and suggestions.

## Installation

```bash
python -m pip install youte
```  

## YouTube API key  

To get data from YouTube API, you will need a YouTube API key. Follow YouTube [instructions](https://developers.google.com/youtube/v3/getting-started) to obtain a YouTube API key if you do not already have one.

## Configure API key (recommended)

You can save your API key in the youte config file for reuse. To do so, run:

```bash  
youte config add-key
```  

The interactive prompt will ask you to input your API key and name it. The name is used to identify the key, and can be anything you choose.

The prompt will also ask if you want to set the given key as default.

When running queries, if no API key or name is specified, `youte` will automatically use the default key.

### Manually set a key as default  

If you want to manually set an existing key as a default, run:  

```bash  
youte config set-default <name-of-existing-key>
```

Note that what is passed to this command is the _name_ of the API key, not the API key itself. It follows that the API key has to be first added to the config file using `youte config add-key`. If you use a name that has not been added to the config file, an error will be raised.

#### See the list of all keys  

To see the list of all keys, run:  

```bash  
youte config list-keys
```  

The default key, if there is one, will have an asterisk next to it.

#### Remove a key

To remove a stored key, run:

```bash
youte config remove <name-of-key>
```

#### About the config file  

youte's config file is stored in a central place whose exact location depends on the running operating system:  

- Linux/Unix: ~/.config/youte/   
- Mac OS X: ~/Library/Application Support/youte/
- Windows: C:\Users\\\<user>\\AppData\Roaming\youte

## search

Searching can be as simple as:

```bash
youte search <search-terms> --key <API-key> --outfile <name-of-file.json>
# OR
youte search <search-terms> --key <API-key> -o <name-of-file.json>
```

If you have a default key set up using `youte config`, then there is no need to specify an API key using `--key`.

This will return the maximum number of results pages (around 12-13) matching the search terms and store them in a JSON file. Unlike version 1.3, youte 2.0 does not print results to the terminal. Instead, `--outfile` is now a required option. <search-terms> and `--outfile` must be specified. 

In the search terms, you can also use the Boolean NOT (-) and OR (|) operators to exclude videos or to find videos that match one of several search terms. If the terms contain spaces, the entire search term value has to be wrapped in quotes.

Use the flag `--pretty` to pretty format the JSON output.

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

Raw JSONs from YouTube API contain request metadata and nested fields. You can tidy these data into a CSV or a flat JSON using `--tidy-to`. The default format that youte will tidy raw JSON into will be CSV.

```bash
youte search <search-terms> --tidy-to <file.csv>
```

Specify `--format json` if you want to tidy raw data into an array of flat JSON objects.

```bash
youte search <search-terms> --tidy-to <file-name.json> --format json
```

`--tidy-to` option is available for all `youte` commands that retrieve data, and works the same way.

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

The `--from` and `--to` options allow you to restrict your search to a specific period. The input values have to be in ISO format (YYYY-MM-DD). Currently, all dates and times in youte are in UTC.

#### Restrict by type

The `--type` option specifies the type of results returned, which by default is videos. The accepted values are `channel`, `playlist`, `video`, or a combination of these three. If more than one type is specified, separate each by a comma.

```shell
youte search <search-terms> --limit 5 --type playlist,video
```

#### Restrict by language and region

The `--lang` returns results most relevant to a language. Not all results will be in the specified language: results in other languages will still be returned if they are highly relevant to the search query term. To specify the language, use [ISO 639-1 two letter code](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes), except that you should use the values `zh-Hans` for simplified Chinese and `zh-Hant` for traditional Chinese.

The `--region` returns results viewable in a region. To specify the region, use [ISO 3166-1 alpha-2](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2). Note that this option does *not* filter videos uploaded in that region, but rather videos that can be _viewed_ in that region.

The `--location` and `--radius` options define a circular geographic area to filter videos that specify, in their metadata, a location within this area. This is *not* a robust and reliable way to geolocate YouTube videos, and hence should be used with care.

-  `--location` takes in 2 values - the latitude/longitude coordinates that represent the centre of the area
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

`youte videos` takes in one or multiple video IDs and retrieve all public metadata for those videos. This complements results returned from `youte search`, as they contain only limited information.

```shell
youte hydrate <resource-id>.... --outfile <file.json>
```

You can put as many IDs as you need, separating each with a space.

Like search, you can also tidy the data to a CSV using the `--tidy-to` option.

```shell
youte hydrate <resource-id>... --outfile <file.json> --tidy-to <file-name.csv>
```

### Use IDs from text file

You can hydrate a list of video ids stored in a text file by using `--file-path` or `-f`. The text file should contain a line-separated list of video ids, with no header.

```shell
youte hydrate -f <id-file.csv>
```

This option is often used in combination with `youte dehydrate`, which retrieves the ids from raw JSON returned by `youte search` and stores them in a text file.

## channels

`youte channels` works the same as `youte videos`, except it retrieves channel metadata given channel ids.

## comments

`youte comments` retrieves top-level comments (comment threads) on one or multiple videos or channels. It takes in a list of ids and a flag indicating which type these ids are (i.e. videos or channels).

To retrieve comments on videos, specify the video ids and pass the `--by-video-id` or `-v` flag.

```shell
youte comments <id>... --by-video-id --outfile <file.json>
#OR
youte comments <id>... -v --outfile <file.json>
```

To retrieve comments on channels, specify channel ids and pass the `--by-channel-id` or `-c` flag.

```bash
youte comments <id>... --by-channel-id --outfile <file.json>
OR
youte comments <id>... -c --outfile <file.json>
```

If neither of the flags are specified, `youte comments` will assume the ids are thread ids and retrieve the full metadata for those threads.

You can search within the threads and filter threads that match the search terms, by using the `--query` or `-q` option.

```bash
youte comments <ids>... -v --outfile <file.json> -q "search term"
```

## replies

While `youte comments` only retrieve top-level comment threads, if those threads have replies, they can be retrieved using `youte replies`. `youte replies` takes a list of thread ids and return the replies to those threads.

```shell
youte replies <ids>... --outfile <file.json>
```

## related-to

`related-to` retrieves videos related to a video.

```shell
youte related-to <video-ids>... -o <file.json>
```

If multiple video IDs are inputted, youte will iterate through each video ID separately, retrieving all related videos to each video, one by one.

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

## chart

`youte chart` retrieves the most popular videos in a region, specified by [ISO 3166-1 alpha-2 country codes](https://www.iso.org/obp/ui/#search). If no argument or option is given, it retrieves the most popular videos in the United States.

For example:

```shell
youte chart <region-code> -o <file.json>
```

## dehydrate

`dehydrate` extracts the IDs from a JSON file returned from YouTube API.

```shell
youte dehydrate <file-name.json>
```

```{.shell .no-copy}
Options:
  -o, --output FILENAME  Output text file to store IDs in
```

## YouTube API Quota system and youte handling of quota 

Most often, there is a limit to how many requests you can make to YouTube API per day. YouTube Data API uses a quota system, whereby each request costs a number of units depending on the endpoint the request is made to.

For example:  

- search endpoint costs 100 units per request  
- video, channel, commentThread, and comment endpoints each costs 1 unit per request  

Free accounts get an API quota cap of 10,000 units per project per day, which resets at midnight Pacific Time.

At present, you can only check your quota usage on the [Quotas](https://console.developers.google.com/iam-admin/quotas) page in the API Console. It is not possible to monitor quota usage via metadata returned in the API response. `youte` does not monitor quota usage.

