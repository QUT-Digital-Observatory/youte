# youte  

A command line utility to get YouTube video metadata and comments from YouTube API. Currently still in beta development. Any feedback or suggestion is most welcome.

## Installation

```shell
pip install youte
```  

## Initial set up  

### YouTube API key  

To get data from YouTube API, you will need a YouTube API key. Follow YouTube [instructions](https://developers.google.com/youtube/v3/getting-started) to obtain a YouTube API key if you do not already have one.  

### Set up youte  

`youte` requires a YouTube API key to be stored in a *config* file, to run YouTube data collection. To set up your YouTube API key with youte, run:  

```shell  
youte config add-key
```  

The interactive prompt will ask you to input your API key, as well as a "name" for that key. The name is used to identify the key, and can be anything you choose.

The program will also ask if you want to set the given key as default.

When doing a youte search, if you don't specify an API key name via `--name`, youte will use the default key if there is one, or raise an error if there is not.  

#### Manually set a key as default  

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

#### Delete a key

To remove a stored key, run:

```shell
youte config remove <name-of-key>
```

#### About the config file  

youte's config file is stored in a central place whose exact location depends on the running operating system:  

- Linux/Unix: ~/.config/youte/   
- Mac OS X: ~/Library/Application Support/youte/
- Windows: C:\Users\\\<user>\\AppData\Roaming\youte  

The config file stores API keys, as well as the quota usage associated with each API key.  

## Search  

```commandline  
Usage: youte search [OPTIONS] QUERY OUTPUT

  Do a YouTube search.

Options:
  --from TEXT                     Start date (YYYY-MM-DD)
  --to TEXT                       End date (YYYY-MM-DD)
  --name TEXT                     Name of the API key (optional)
  --order [date|rating|relevance|title]
                                  Sort results  [default: date]
  --safe-search [none|moderate|strict]
                                  Include or exclude restricted content
                                  [default: none]
  --max-quota INTEGER             Maximum quota allowed  [default: 10000]
  --help                          Show this message and exit.
```  

### Example  

```commandline  
youte search 'study with me' --from 2022-08-01 --to 2022-08-07 study_with_me.jsonl
youte search gaza --from 2022-07-25 --name user_2 --safe-search=moderate --order=title gaza_ids.jsonl
```  

### Arguments and options  

#### `QUERY`  

The terms to search for. You can also use the Boolean NOT (-) and OR (|) operators to exclude videos or to find videos that match one of several search terms. If the terms contain spaces, the entire QUERY value has to be wrapped in quotes.  

```commandline  
youte search "koala|australia zoo -kangaroo" aussie_animals.jsonl
```  

If you are looking for exact phrases, the exact phrases can be wrapped in double quotes, then wrapped again by single quotes.  

```commandline  
youte search '"australia zoo"' aussie_zoo.jsonl
```  

#### `OUTPUT`  

Path of the output file where raw JSON responses will be stored. Must have `.json` file endings (e.g., `.json` or `.jsonl`). If the output file already exists, `youte` will **_update_** the existing file, instead of overwriting it.

#### `--from` (optional)  

Start date limit for the search results returned - the results returned by the API should only contain videos created on or after this date (UTC time, which is the default time zone for the YouTube API). Has to be in ISO format (YYYY-MM-DD).

#### `--to` (optional)  

End date limit for the search results returned - the results returned by the API should only contain videos created on or before this date (UTC time, which is the default time zone for the YouTube API). Has to be in ISO format (YYYY-MM-DD).

#### `--name` (optional)  

Name of the API key, if you don't want to use the default API key or if no default API key has been set.  

The API key name has to be added to the config file first using `youte config add-key`.  

#### `--max-quota` (optional)  

Change the maximum quota that your API key is allowed to consume. The default value is 10,000, which is the standard quota cap for all Google accounts. Read more about YouTube API's quota system [below](#youtube-api-quota-system-and-youte-handling-of-quota).  

### Saving search progress  

Searching is very expensive in terms of API quota (100 units per search results page). Therefore, `youte` saves the progress of a search so that if you exit the program prematurely, either by accident or on purpose, you can resume the search to avoid wasting valuable quota.

Specifically, when you exit the program in the middle of a search, a prompt will ask if you want to save its progress. If yes, all the recorded plus unrecorded search page tokens are saved in a SQLite database in a hidden `.youte.history` folder inside your current directory. The name of the database is what is passed as the `OUTPUT` with the `.json` extension removed. If you rerun the same search in the same directory, you can choose to resume the progress from that database. This database will be deleted once all search results have been returned.

```commandline  
$youte search taiwan --from 2022-08-08 --output test.jsonl  

Getting API key from config file.  
Getting page 1 ⏳  
Getting page 2 ⏳  

# exit the program  
Do you want to save your current progress? [y/N]: # y  

# resume search  
$youte search taiwan --from 2022-08-08 --output test.jsonl  

Getting API key from config file.  

        A history file '.youte.history/taiwan.db' is detected in your current directory.
        Do you want to resume progress from this history file?
        If you are at all unsure, say No. [y/N]:
```  

## Hydrate a list of IDs

```commandline  
Usage: youte hydrate [OPTIONS] FILEPATH OUTPUT

  Hydrate video or channel ids.

  Get all metadata for a list of video or channel IDs. By default, the
  function hydrates video IDs.

Options:
  --channel            Hydrate channel IDs instead of video IDs
  --name TEXT          Name of the API key (optional)
  --max-quota INTEGER  Maximum quota allowed  [default: 10000]
  --help               Show this message and exit.
```  

### Examples  

```commandline  
youte hydrate video_ids.csv videos.jsonl  
youte hydrate channel_ids.txt --channel channels.jsonl  
```  

### Arguments and options  

#### `FILEPATH`  

Path of a text file (e.g., `.csv` or `.txt`) containing a line-separated list of video or channel IDs.  

#### `--channel`  

Pass this flag if the IDs to be hydrated are channel IDs and not video IDs.  

## Get all comments of a video or all replies to a top-level comment thread  

```commandline  
Usage: youte list-comments [OPTIONS] FILEPATH OUTPUT

  Get YouTube comments from a list of comment thread or video ids.

  By default, hydrate all comments from a list of comment ids.

Options:
  -p, --by-parent      Get all replies to a comment thread
  -v, --by-video       Get all comments for a video ID
  --max-quota INTEGER  Maximum quota allowed  [default: 10000]
  --name TEXT          Name of the API key (optional)
  --help               Show this message and exit.
```  

### Example  

```  
youte list-comments video_ids.csv -v comments_for_videos.jsonl  
youte list-comments comment_ids.csv comments.jsonl  
youte list-comments comment_ids.csv -p replies_to_comments.jsonl  
```  

### Arguments and options  

#### `FILEPATH`  

Path of a text file containing a line-separated list of videos, channels, or comments IDs.  

#### `--by-parent`, `--by-video`  

- Get all replies to a parent comment (`--by-parent`, `-p`)  
- Get all comments under a video (`--by-video`, `-v`)  

If none of these flags are passed, the `list-comments` command works similarly to `hydrate` - getting full data for a list of comment IDs.   

Only one flag can be used in one command.  

## Tidy JSON responses  

```commandline  
Usage: youte tidy [OPTIONS] FILEPATH OUTPUT

  Tidy raw JSON response into relational SQLite databases

Options:
  --help  Show this message and exit.
```  

The `tidy` command will detect the type of resources in the JSON file (i.e. video, channel, search results, or comments) and process the data accordingly. It's important that each JSON file contains just **one** type of resource.  

## YouTube API Quota system and youte handling of quota  

Most often, there is a limit to how many requests you can make to YouTube API per day. YouTube API uses a quota system in which each request costs a number of units depending on the endpoint the request is made to.  

For example:  

- search endpoint costs 100 units per request  
- video, channel, commentThread, and comment endpoints each costs 1 unit per request  

Free accounts get an API quota cap of 10,000 units per project per day, which resets at midnight Pacific Time. Hence the default maximum quota value is set to be 10,000 in `youte`.  

At present, you can only check your quota usage on the [Quotas](https://console.developers.google.com/iam-admin/quotas?pli=1&project=google.com:api-project-314373636293&folder=&organizationId=) page in the API Console. It is not possible to monitor quota usage via metadata returned in the API response.   

Therefore, youte manually monitors quota by keeping counts of requests made and logging their quota usage to the config file. If the maximum quota has been reached, youte handles it by putting the program to sleep until quota reset time (midnight Pacific) before re-running the collector. This is a makeshift approach and does not guarantee perfectly accurate data, especially when you try to collect data on multiple computers using the same API key. Any suggestion for solutions is most welcome.
