# youte  

A command line utility to get YouTube video metadata and comments from YouTube Data API.

## Installation

```shell
python -m pip install youte
```  

## YouTube API key  

To get data from YouTube API, you will need a YouTube API key. Follow YouTube [instructions](https://developers.google.com/youtube/v3/getting-started) to obtain a YouTube API key if you do not already have one.

## Configure API key (recommended)

You can save your API key in the youte config file for reuse. To do so, run:

```shell  
youte config add-key
```  

The interactive prompt will ask you to input your API key and name it. The name is used to identify the key, and can be anything you choose.

The prompt will also ask if you want to set the given key as default.

When running queries, if no API key or name is specified, `youte` will automatically use the default key.

### Manually set a key as default  

If you want to manually set an existing key as a default, run:  

```shell  
youte config set-default <name-of-existing-key>
```

Note that what is passed to this command is the _name_ of the API key, not the API key itself. It follows that the API key has to be first added to the config file using `youte config add-key`. If you use a name that has not been added to the config file, an error will be raised.

#### See the list of all keys  

To see the list of all keys, run:  

```shell  
youte config list-keys
```  

The default key, if there is one, will have an asterisk next to it.

#### Remove a key

To remove a stored key, run:

```shell
youte config remove <name-of-key>
```

#### About the config file  

youte's config file is stored in a central place whose exact location depends on the running operating system:  

- Linux/Unix: ~/.config/youte/   
- Mac OS X: ~/Library/Application Support/youte/
- Windows: C:\Users\\\<user>\\AppData\Roaming\youte

## Search  

```commandline  
Usage: youte search [OPTIONS] QUERY [OUTPUT]

  Do a YouTube search.

  QUERY: search query

  OUTPUT: name of json file to store output data

Options:
  --from TEXT                     Start date (YYYY-MM-DD)
  --to TEXT                       End date (YYYY-MM-DD)
  --type TEXT                     Type of resource to search for  [default:
                                  video]
  --name TEXT                     Specify an API name added to youte config
  --key TEXT                      Specify a YouTube API key
  --order [date|rating|relevance|title|videoCount|viewCount]
                                  Sort results  [default: date]
  --safe-search [none|moderate|strict]
                                  Include or exclude restricted content
                                  [default: none]
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
  --max-results INTEGER RANGE     Maximum number of results returned per page
                                  [default: 50; 0<=x<=50]
  -l, --limit INTEGER RANGE       Maximum number of result pages to retrieve
                                  [1<=x<=13]                           
  --resume TEXT                   Resume progress from this file
  --to-csv PATH                   Tidy data to CSV file
  --help                          Show this message and exit.

```  

### Example  

```commandline  
youte search 'study with me' --from 2022-08-01 --to 2022-08-07

youte search gaza --from 2022-07-25 --name user_2 --safe-search moderate --order=title gaza.json
```

### Arguments and options  

#### `QUERY`  

The terms to search for. You can also use the Boolean NOT (-) and OR (|) operators to exclude videos or to find videos that match one of several search terms. If the terms contain spaces, the entire QUERY value has to be wrapped in quotes.  

```commandline  
youte search "koala|australia zoo -kangaroo"
```  

If you are looking for exact phrases, the exact phrases can be wrapped in double quotes, then wrapped again in single quotes.  

```commandline  
youte search '"australia zoo"' aussie_zoo.jsonl
```  

#### `OUTPUT` (optional)

Path of the output file where raw JSON responses will be stored. Must have `.json` file endings (e.g., `.json` or `.jsonl`). If the output file already exists, `youte` will **_update_** the existing file, instead of overwriting it.

If no OUTPUT argument is passed, results will be printed to the terminal.

#### `--from` (optional)  

Start date limit for the search results returned - the results returned by the API should only contain videos created on or after this date (UTC time, which is the default time zone for the YouTube API). Has to be in ISO format (YYYY-MM-DD).

#### `--to` (optional)  

End date limit for the search results returned - the results returned by the API should only contain videos created on or before this date (UTC time, which is the default time zone for the YouTube API). Has to be in ISO format (YYYY-MM-DD).

#### `--name` (optional)  

Name of the API key, if you don't want to use the default API key or if no default API key has been set.  

The API key name has to be added to the config file first using `youte config add-key`.  

#### `--key` (optional)

The API key to use, if you want to use a key not configured with youte.

#### `--type` (optional)

Type of Youtube resource to retrieve. Can be one type or a comma-separated list of acceptable types, which are `channel`, `playlist`, `video`.

#### `--limit` (optional)

Specify the number of result pages to retrieve. Useful when you want to test search terms without using up your quota. 

#### `--order` (optional)

Specify how results will be sorted.

- `date`: Resources are sorted in reverse chronological order based on the date they were created (default value).
- `rating`: Resources are sorted from highest to lowest rating.
- `relevance`: Resources are sorted based on their relevance to the search query.
- `title` – Resources are sorted alphabetically by title.
- `videoCount` – Channels are sorted in descending order of their number of uploaded videos.
- `viewCount` – Resources are sorted from highest to lowest number of views. For live broadcasts, videos are sorted by number of concurrent viewers while the broadcasts are ongoing.

#### `--safe-search` (optional)

Specify whether restricted content is included or exclude.

#### `--video-duration` (optional)

Include videos of a certain duration.

#### `--channel-type` (optional)

Restrict search to a particular type of channel. `--type` has to include `channel`.

#### `--caption` (optional)

Restrict search to videos with or without captions. `--type` has to include `video`.

#### `--definition` (optional)

Restrict search to videos with a certain definition. `--type` has to include `video`.

#### `--dimension` (optional)

Restrict search to 2D or 3D videos. `--type` has to include `video`.

#### `--embeddable` (optional)

Only search for embeddable videos. `--type` has to include `video`.

#### `--license` (optional)

Only include videos with a certain licence.

#### `--max-results` (optional)

Maximum number of results returned per page. The default value is 50.

#### `--resume` (optional)

Resume progress from a progress file.

Searching is very expensive in terms of API quota (100 units per search results page). Therefore, `youte` saves the progress of a search so that if you exit the program prematurely, you can choose to resume the search to avoid wasting valuable quota.

When you exit the program in the middle of a search, a prompt will ask if you want to save progress. If yes, all search page tokens are stored to a database in the **.youte.history** folder inside your current directory. 

The name of the progress file is printed on the terminal, as demonstrated below:

```commandline
Do you want to save your current progress? [y/N]: y
Progress saved at /home/boyd/Documents/youte/.youte.history/search_1669178310.db
To resume progress, run the same youte search command and add `--resume search_1669178310`
```

To resume progress of this query, run the same query again and add `--resume <NAME OF PROGRESS>`. 

You can also run `youte list-history` to see the list of resumable progress files found in ***.youte.history*** folder inside your current directory.

#### `--to-csv` (optional)  

Tidy results into a CSV file.

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

