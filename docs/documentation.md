---
title: "youte documentation"
---

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

In the interactive prompt, enter your API key and give it a name. The name is used to identify the key, and can be anything you choose.

You can also choose to set the key as default. When running queries, if no API key or name is specified, `youte` will automatically use the default key.

### See the list of all keys

To see the list of all keys and their names stored in the config, run:

```shell
youte config list-keys
```

The default key, if there is one, will have an asterisk next to it.

### Manually set a key as default

If you want to manually set an existing key as a default, run:

```shell
youte config set-default <name-of-existing-key>
```

Note that what is passed to this command is the _name_ of the API key, not the API key itself. It follows that the API key has to be first added to the config file using `youte config add-key`. If you use a name that has not been added to the config file, an error will be raised.



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

```shell
youte search <search-terms> --key <API-key>
```

If you have a default key set up using `youte config`, then there is no need to specify an API key.

This will return the maximum number of results pages (around 12-13) matching the search terms and print them to the shell. Instead of having the JSON printed to the shell, you can specify a JSON file to save results to with the `-o` or `--output` option.

```shell
youte search <search-terms> -o <file-name.json>
```

In the search terms, you can also use the Boolean NOT (-) and OR (|) operators to exclude videos or to find videos that match one of several search terms. If the terms contain spaces, the entire search term value has to be wrapped in quotes.

### Limit

Searching is very expensive in terms of API usage - each results page uses up 100 points of your daily quota. Therefore, you can limit the number of result pages returned, so that a search doesn't go on and exhaust your API quota.

```shell
youte search <search-terms> --limit 5
```

### Export to CSV

If you want tidy data in a spreadsheet format, pass the `--to-csv` option and name of the CSV file.

```shell
youte search <search-terms> --limit 5 --to-csv <file-name.csv>
```

You can save results in both JSON and CSV format by specifying both a JSON name and a `--to-csv` option.

```shell
youte search <search-terms> -o <file-name.json> --limit 5 --to-csv <file-name.csv>
```

### Advanced search

There are multiple filters to refine your search. A full list of these are provided below:

``` {.bash .no-copy}
Options:
  --from TEXT                     Start date (YYYY-MM-DD)
  --to TEXT                       End date (YYYY-MM-DD)
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
```

#### Restrict by date range

The `--from` and `--to` options allow you to restrict your search to a specific period. The input values have to be in ISO format (YYYY-MM-DD). Currently, all dates and times in youte are in UTC.

#### Restrict by type

The `--type` option specifies the type of results returned, which by default is videos. The accepted values are `channel`, `playlist`, `video`, or a combination of these three. If more than one type is specified, separate each by a comma.

```shell
youte search <search-terms> --limit 5 --type channel,video
```

#### Restrict by language and region

The `--lang` returns results most relevant to a language. Not all results will be in the specified language: results in other languages will still be returned if they are highly relevant to the search query term.. To specify the language, use [ISO 639-1 two letter code](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes), but you should use the values `zh-Hans` for simplified Chinese and `zh-Hant` for traditional Chinese.

The `--region` returns results viewable in a region. It does *not* filter videos uploaded in that region only. To specify the region, use [ISO 3166-1 alpha-2](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2).

### Sort results

The `--order` option specifies how results will be sorted. The following values are accepted:

- `date`: Resources are sorted in reverse chronological order based on the date they were created (default value).
- `rating`: Resources are sorted from highest to lowest rating.
- `relevance`: Resources are sorted based on their relevance to the search query.
- `title` – Resources are sorted alphabetically by title.
- `videoCount` – Channels are sorted in descending order of their number of uploaded videos.
- `viewCount` – Resources are sorted from highest to lowest number of views. For live broadcasts, videos are sorted by number of concurrent viewers while the broadcasts are ongoing.

### Save and resume searches

As explained above, searching costs a lot of API units and can quickly use up your API quota. Ideally we would want to run as few searches as possible and avoid running the same search multiple times.

youte saves the progress of a search so that if you exit the program prematurely, you can choose to resume the search to avoid wasting valuable quota.

When you exit the program in the middle of a search (by pressing Ctrl + C), a prompt will ask if you want to save progress. If yes, all search page tokens are stored to a database in a *.youte.history* folder inside your current directory.

The ID of the search is saved and printed to the shell, as demonstrated below:

``` {.shell .no-copy}
Do you want to save your current progress? [y/N]: y
Progress saved at /home/boyd/Documents/youte/.youte.history/search_1669178310.db
To resume progress, run the same youte search command and add `--resume search_1669178310`
```

To resume progress of this query, simply run `youte search --resume <search-id>`. Once a query is completed, the search ID is removed.

#### Search history

Run `youte history` to see the list of resumable search IDs inside the ***.youte.history*** folder. To know the details of each search, run `youte history -v` or `youte history --verbose`.

## hydrate

`youte hydrate` takes a list of resource IDs, and get the full data associated with them. The resources can be videos, channels, or comments.

```shell
youte hydrate <resource-id>....
```

You can put as many IDs as you need, separating each with a space. By default, youte takes these resource IDs as videos. You can specify the kind of resources with the `---kind` option.

```shell
youte hydrate <resource-id>... --kind channels
```

`--kind` accepts these 3 values: `channels`, `videos`, `comments`. Only one kind can be set at a time. It follows that all IDs have to be the same kind.

To store results in a file, pass the `--output` or `-o` option.

```shell
youte hydrate <resource-id>... --output <file-name.json>
```

Like search, you can also export the data to CSV using the `--to-csv` option.

```shell
youte hydrate <resource-id>... --to-csv <file-name.csv>
```

### Get IDs from text file

You can hydrate a list of resource IDs stored in a text file by using `--file-path` or `-f`. The text file should contain a line-separated list of IDs, with no header. One file should contain one type of IDs.

```shell
youte hydrate -f <id-file.csv>
```

## get-comments

get-comments takes in one or a list of video or thread IDs, and return all comments under that video or thread. If the item is a video, get-comments retrieves all the top level comments (threads) of that video. If the item is a thread, get-comments retrieves all replies to that thread, if there are any.

You specify whether the ID belongs to a video or thread by the `-v` and `-t` flag.

```shell
youte get-comments <video-id> -v
youte get-comments <thread-id> -t
```

Only one flag can be used in one command. If none of these flags are passed, `get-comments` will not return anything.

Other things you can do with get-comments are similar to `hydrate`:

``` {.shell .no-copy}
Options:
  -o, --output FILENAME
  -f, --file-path TEXT   Get IDs from file
  --to-csv PATH          Tidy data to CSV file
```


## get-related

get-related retrieves a list of videos related to a video/multiple videos.

```shell
youte get-related <video-id>...
```

If multiple video IDs are inputted, youte will iterate through each video ID separately, retrieving all related videos to each video, one by one.

``` {.shell .no-copy}
Options:
  -f, --file-path PATH            Get IDs from file
  -o, --output FILENAME           Name of JSON file to store output
  --safe-search [none|moderate|strict]
                                  Include or exclude restricted content
                                  [default: none]
  --name TEXT                     Specify an API key name added to youte
                                  config
  --key TEXT                      Specify a YouTube API key
  --max-results INTEGER RANGE     Maximum number of results returned per page
                                  [default: 50; 0<=x<=50]
  --to-csv PATH                   Tidy data to CSV file
  --help                          Show this message and exit.
```

## most-popular

most-popular retrieves the most popular videos in a region, specified by [ISO 3166-1 alpha-2 country codes](https://www.iso.org/obp/ui/#search). If no argument or option is given, it retrieves the most popular videos in the United States.

You specify the region with the `-r` or `--region` option.

For example:

```shell
youte most-popular -r <region-code>
```

``` {.shell .no-copy}
Usage: youte most-popular [OPTIONS] [OUTPUT]

  Return the most popular videos for a region and video category

  By default, if nothing is else is provided, the command retrieves the most
  popular videos in the US.

  OUTPUT: name of JSON file to store results

Options:
  -r, --region-code TEXT  ISO 3166-1 alpha-2 country codes to retrieve videos
  --to-csv PATH           Tidy data to CSV file
  --help                  Show this message and exit.
```

## tidy

tidy tidies the raw JSON into an SQlite database. You can select multiple JSON files at the same time and tidy them into the same database.

```shell
youte tidy <file-name.json>... <output-db.db>
```

The `tidy` command will detect the type of resources in the JSON file (i.e. video, channel, search results, or comments) and process the data accordingly. It's important that each JSON file contains just **one** type of resource. You can specify multiple JSON files, but the final argument has to be the output database.


### Database schemas

`youte tidy` processes JSON data into different schemas depending on the type of resource in the JSON file. Here are the schema names with their corresponding YouTube resources.

| Resource                             | Schema         |
|--------------------------------------|----------------|
| Search results (from `youte search`) | search_results |
| Videos (from `youte hydrate`, `youte most-popular`, `youte get-related`)  | videos         |
| Channels (from `youte hydrate`)      | channels       |
| Comment threads (from `youte get-comments -v`) | comments       |
| Replies to comment threads (from `youte get-comments -t`)           | comments       |

### Data dictionary

Refer to [YouTube Data API](https://developers.google.com/youtube/v3/docs) for definitions of the properties or fields returned in the data. Some fields such as `likeCount`, `viewCount`, and `commentCount` will be empty if these statistics are disabled.

## dehydrate

`dehydrate` extracts the IDs from a JSON file returned from YouTube API.

```shell
youte dehydrate <file-name.json>
```

```{.shell .no-copy}
Options:
  -o, --output FILENAME  Output text file to store IDs in
```
