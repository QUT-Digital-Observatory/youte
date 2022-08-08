# youtupy

A command line utility to get YouTube video metadata from Youtube API.

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

## Initial set up

### YouTube API key

To get data from YouTube API, you will need a YouTube API key. Follow YouTube [instructions](https://developers.google.com/youtube/v3/getting-started) to obtain a YouTube API key if you do not already have one.

### Set up youtupy

youtupy requires a YouTube API key, stored in a *config* file, to run YouTube searches. To set up your YouTube API key with youtupy, run:

```shell
youtupy configure add-key
```

The interactive prompt will ask you to input your API key, as well as a "name" for that key. The key name is used to identify the key, and can be anything you choose.

**Set a key as default**

The program will also ask if you want to set the given key as default.

When doing a youtupy search, if you don't specify an API key name, youtupy will use the default key if there is one, or raise an error if there is not.

If you want to manually set an existing key as a default, run:

```shell
youtupy configure set-default <name-of-existing-key>
```

Note that the *name* of the API key is passed to this command, not the API key itself. It follows that the API key has to be first added to the config file using `youtupy configure add-key`. If you use `set-default` with a key that has not been added to the config file, an error will be raised.

**See the list of all keys**

To see the list of all keys, run:

```shell
youtupy configure list-keys
```

The default key, if there is one, will have an asterisk next to it.

#### About the config file

youtupy's config file is stored in a central place, whose exact location depends on the running operating system:

- Linux/Unix: ~/.config/youtupy/ 
- Mac OS X: ~/Library/Application Support/youtupy
- Windows: C:\Users\<user>\AppData\Roaming\youtupy

The config file stores API keys, as well as the quota usage associated with each API key.

## (all sections below are out-of-date)
New content to be updated soon.

## Run a search


`youtupy search` is the command that collects data from YouTube API.

```shell
youtupy search --help

Usage: youtupy search [OPTIONS] QUERY

  Collect data from Youtube API.

Options:
  -o, --output TEXT    Output database. Must end in `.db`
  --from TEXT          Start date (YYYY-MM-DD)
  --to TEXT            End date (YYYY-MM-DD)
  --max-quota INTEGER  Maximum quota allowed  [default: 10000]
  --name TEXT          Name of the API key (optional)
  --comments           Get video comments
  --replies            Get replies to video comments
  --help               Show this message and exit.
```

### Example

```shell
youtupy search 'koala' --from 2022-04-01 --to 2022-06-01 --comments --replies --output aussie_animals.db
```

### Arguments and options

#### `QUERY`

The terms to search for. You also use the Boolean NOT (-) and OR (|) operators to exclude videos or to find videos that are associated with one of several search terms. If the terms contain spaces, the entire `QUERY` value has to be wrapped in single quotes. 

```shell
youtupy search 'koala|australia zoo -kangaroo' --output aussie_animals.db
```

If you are looking for exact phrases, the exact phrases can be wrapped in double quotes, then wrapped again by single quotes.

```shell
youtupy search '"australia zoo"' --output aussie_zoo.db
```

#### `--from` (optional)

Start date limit for the search results returned - the results returned by the API should only contain videos created on or after this date. Has to be in ISO format (YYYY-MM-DD).

If neither `--from` nor `--to` parameters is specified (i.e. no date limit is specified), you'll be requesting a potentially large amount of data from the API, which can use up your available quota. In this case, a confirmation prompt will appear before you can continue.

#### `--to` (optional)

End date limit for the search results returned - the results returned by the API should only contain videos created on or before this date. Has to be in ISO format (YYYY-MM-DD).

If neither `--from` nor `--to` parameters is specified (i.e. no date limit is specified), you'll be requesting a potentially large amount of data from the API, which can use up your available quota. In this case, a confirmation prompt will appear before you can continue.

#### `--comments` (optional)

Specifies that comment data should be collected as well. This will only collect the *comment threads*, meaning top-level comments. Replies to comments are not collected.

#### `--replies` (optional)

Specifies that replies to comments should be collected as well. This will only work when `--comments` is also specified.

#### `-o`, `--output`

Path of the SQLite database where data will be stored. Has to end in `.db` or an `InvalidFileName` error will be raised.
	
Currently, youtupy only works properly with one database containing data from the same *search parameters* - query, start date and/or end date. For example, you will encounter data errors if you run the following:

```shell
youtupy search 'koala' --from 2022-05-01 --output aussie_animals.db
youtupy search 'kangaroo' --from 2022-05-01 --output aussie_animals.db
```

In the above example, the same database is used to store data from searches using two different search terms. You will run to issues if you do this. Similar issues can occur if you run the following:

```shell
youtupy search 'koala' --from 2022-05-01 --output aussie_animals.db
youtupy search 'koala' --from 2022-04-01 --to 2022-06-01 --output aussie_animals.db
```

In the above example, although the same query is used, different date parameters are specified.

Adding `--comments` and `--replies` won't fundamentally change the search parameters and hence won't cause any data issue (apart from giving you more data!).

```shell
# this won't cause any issue
youtupy search 'koala' --from 2022-05-01 --output aussie_animals.db
youtupy search 'koala' --from 2022-05-01 --comments --replies --output aussie_animals.db
```

#### `--name` (optional)

Name of the API key, if you don't want to use the default API key or if no default API key has been set.

The API key name has to be added to the config file first using `youtupy configure add-key`.

#### `--max-quota` (optional)

Change the maximum quota allowed for your API key. The default value is 10,000, which is the standard quota cap for all Google accounts. Read more about YouTube API's quota system [below](#youtube-api-quota-system-and-youtupy-handling-of-quota).

### What happens when `youtupy search` is run

`youtupy search` by default collects data from three YouTube API endpoints: search, video, and channel. First, it collects YouTube search results matching specified search terms using YouTube API's search endpoint. The processed/tidied data are stored in the `search_results` schema in the output database. 

It then collects additional, enriching video and channel metadata for the search results, using YouTube API's video and channel endpoints. The end result is three schemas/tables containing all available metadata on search results, videos, and channels.

If `--comments` and `--replies` are specified, the script goes on to collect comment and reply data for the videos collected from the YouTube search. Comments and replies are stored in `common_threads` and `replies` schema in the same output database.

Along the way, quota usage is recorded in the config file every time an API request is made. More about quota system below.

## YouTube API Quota system and youtupy handling of quota

Most often, there is a limit to how many requests you can make to YouTube API per day. YouTube API uses a quota system in which each request costs a number of units depending on the endpoint the request is made to.

For example:

- search endpoint costs 100 units per request
- video, channel, commentThread, and comment endpoints each costs 1 unit per request

Free GCP accounts get an API quota cap of 10,000 units per project per day, which resets at midnight Pacific Time. Hence the default maximum quota value is set to be 10,000 in youtupy.

At present, you can only check your quota usage on the [Quotas](https://console.developers.google.com/iam-admin/quotas?pli=1&project=google.com:api-project-314373636293&folder=&organizationId=) page in the API Console. Unlike Reddit, it is not possible to monitor quota usage via metadata returned in the API response. 

Therefore, youtupy manually monitors quota by keeping counts of requests made and logging their quota usage to the config file. If the maximum quota has been reached, youtupy handles it by putting the program to sleep until quota reset time (midnight Pacific) before re-running the collector. This is a makeshift approach and does not guarantee perfectly accurate data, especially when you try to collect data on multiple computers using the same API key.


