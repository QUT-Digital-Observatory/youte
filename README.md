# youte  

A command line utility to get YouTube video metadata and comments from YouTube Data API.

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

## Search

Searching can be as simple as:

```bash
youte search <search-terms> --key <API-key> --outfile <name-of-file.json>
```

If you have a default key set up using `youte config`, then there is no need to specify an API key using `--key`.

This will return the maximum number of results pages (around 12-13) matching the search terms and store them in a JSON file. <search-terms> and `--outfile` have to be specified.

In the search terms, you can also use the Boolean NOT (-) and OR (|) operators to exclude videos or to find videos that match one of several search terms. If the terms contain spaces, the entire search term value has to be wrapped in quotes.

Prettify JSON results by using the flag `--pretty`:

```bash
youte search <search-terms> --key <API-key> --outfile <name-of-file> --pretty
```

### Limit pages returned

Searching is very expensive in terms of API usage - a single results page uses up 100 points - 1% of your daily quota. Therefore, you can limit the maximum number of result pages returned, so that a search doesn't go on and exhaust your API quota.

```bash
youte search <search-terms> --max-pages 5
```

### Tidy data

Raw JSONs from YouTube API contain query metadata and nested fields. You can tidy these data into a CSV or a flat JSON using `--tidy-to`. The default format that youte will tidy raw JSON into will be CSV.

```bash
youte search <search-terms> --limit 5 --to-csv <file-name.csv>
```

Specify `--format json` if you want to tidy raw data into an array of flat JSON objects.

```bash
youte search <search-terms> --limit 5 --to-csv <file-name.json> --format json
```

You can save results in both JSON and CSV format by specifying both a JSON name and a `--to-csv` option.

```bash
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

The `--lang` returns results most relevant to a language. Not all results will be in the specified language: results in other languages will still be returned if they are highly relevant to the search query term. To specify the language, use [ISO 639-1 two letter code](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes), except that you should use the values `zh-Hans` for simplified Chinese and `zh-Hant` for traditional Chinese.

The `--region` returns results viewable in a region. It does *not* filter videos uploaded in that region only. To specify the region, use [ISO 3166-1 alpha-2](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2).

### Sort results

The `--order` option specifies how results will be sorted. The following values are accepted:

- `date`: Resources are sorted in reverse chronological order based on the date they were created (default value).
- `rating`: Resources are sorted from highest to lowest rating.
- `relevance`: Resources are sorted based on their relevance to the search query.
- `title` – Resources are sorted alphabetically by title.
- `videoCount` – Channels are sorted in descending order of their number of uploaded videos.
- `viewCount` – Resources are sorted from highest to lowest number of views. For live broadcasts, videos are sorted by number of concurrent viewers while the broadcasts are ongoing.

## Hydrate a list of IDs

`youte hydrate` takes a list of resource IDs, and get the full data associated with them.

```commandline  
Usage: youte hydrate [OPTIONS] [ITEMS]...

  Hydrate YouTube resource IDs.

  Get all metadata for a list of resource IDs. By default, the function hydrates video IDs.

  All IDs passed in the command must be of one kind.

  OUTPUT: name of JSON file to store output

  ITEMS: ID(s) of item as provided by YouTube

Options:
  -o, --output FILENAME
  -f, --file-path TEXT            Get IDs from file
  --kind [videos|channels|comments]
                                  Sort results  [default: videos]
  --name TEXT                     Specify an API name added to youte config
  --key TEXT                      Specify a YouTube API key
  --to-csv PATH                   Tidy data to CSV file
  --help                          Show this message and exit.

``` 

### Examples  

```commandline
# one video
youte hydrate _KrKdj50mPk

# two video
youte hydrate _KrKdj50mPk hpwPciW74b8 --output videos.json

# hydrate channel information and use IDs from a text file
youte hydrate -f channel_ids.txt --kind channel
```

### Arguments and options  

#### `ITEMS`

YouTube resource IDs. If there are multiple IDs, separate each one with a space.

The IDs should all belong to one type, i.e. either video, channel, or comment. For example, you cannot mix both video AND channel IDs in one command.

#### `-f` or `--file-path`  

If you want to use IDs from a text file, specify this option with the path to the text file (e.g., `.csv` or `.txt`). The text file should contain a line-separated list of IDs. 

One file should contain one type of IDs.

#### `--kind` 

Specify which kind of resources the IDs are. The default value is `videos`.

## Get all comments of a video or all replies to a top-level comment thread  

```commandline  
Usage: youte get-comments [OPTIONS] [ITEMS]...

  Get YouTube comments by video IDs or thread IDs.

  OUTPUT: name of JSON file to store output

  ITEMS: ID(s) of item as provided by YouTube

Options:
  -o, --output FILENAME
  -f, --file-path TEXT   Get IDs from file
  -t, --by-thread        Get all replies to a parent comment
  -v, --by-video         Get all comments for a video ID
  --name TEXT            Specify an API name added to youte config
  --key TEXT             Specify a YouTube API key
  --to-csv PATH          Tidy data to CSV file
  --help                 Show this message and exit.
```  

### Example  

```  
# get comments on a video
youte get-comments -v comments_for_videos.json WOoQOd33ZTY

# get replies to a thread
youte get-comments -t replies.json UgxkjPsKbo2pUEAJju94AaABAg
```  

### Arguments and options  

#### `ITEMS`

Video or comment thread IDs (unique identifiers provided by YouTube). If there are multiple IDs, separate each one with a space.

The IDs should all belong to one type, i.e. either video or comment thread. You cannot mix both video AND comment thread IDs in one command.

#### `-f` or `--file-path`  

If you want to use IDs from a text file, specify this option with the path to the text file (e.g., `.csv` or `.txt`). The text file should contain a line-separated list of IDs.

One file should contain one type of IDs (i.e. either video or comment thread). You cannot add both video and comment thread IDs in the same file.

#### `--by-thread`, `--by-video`  

- Get all replies to a comment thread (`--by-thread`, `-t`)  
- Get all comments on a video (`--by-video`, `-v`)  

If none of these flags are passed, the `get-comments` command works similarly to `hydrate` - getting full data for a list of comment IDs.

Only one flag can be used in one command.

## Tidy JSON responses  

```commandline  
Usage: youte tidy [OPTIONS] FILEPATH... OUTPUT

  Tidy raw JSON response into relational SQLite databases

Options:
  --help  Show this message and exit.
```  

The `tidy` command will detect the type of resources in the JSON file (i.e. video, channel, search results, or comments) and process the data accordingly. It's important that each JSON file contains just **one** type of resource. You can specify multiple JSON files, but the final argument has to be the output database. 


### Database schemas

`youte tidy` processes JSON data into different schemas depending on the type of resource in the JSON file. Here are the schema names with their corresponding YouTube resources.

| Resource                             | Schema         |
|--------------------------------------|----------------|
| Search results (from `youte search`) | search_results |
| Videos                               | videos         |
| Channels                             | channels       |
| Comment threads (top-level comments) | comments       |
| Replies to comment threads           | comments       |


### Data dictionary

Refer to [YouTube Data API](https://developers.google.com/youtube/v3/docs) for definitions of the properties or fields returned in the data. Some fields such as `likeCount`, `viewCount`, and `commentCount` will show as null if these statistics are disabled.


## Dehydrate

```commandline  
Usage: youte dehydrate [OPTIONS] INFILE

  Extract an ID list from a file of YouTube resources

  INFILE: JSON file of YouTube resources

Options:
  -o, --output FILENAME  Output text file to store IDs in
  --help                 Show this message and exit.
```

## YouTube API Quota system and youte handling of quota 

Most often, there is a limit to how many requests you can make to YouTube API per day. YouTube Data API uses a quota system, whereby each request costs a number of units depending on the endpoint the request is made to.

For example:  

- search endpoint costs 100 units per request  
- video, channel, commentThread, and comment endpoints each costs 1 unit per request  

Free accounts get an API quota cap of 10,000 units per project per day, which resets at midnight Pacific Time.

At present, you can only check your quota usage on the [Quotas](https://console.developers.google.com/iam-admin/quotas?pli=1&project=google.com:api-project-314373636293&folder=&organizationId=) page in the API Console. It is not possible to monitor quota usage via metadata returned in the API response.   

`youte` does not monitor quota usage. However, it handles errors when quota is exceeded by sleeping until quota reset time. 

