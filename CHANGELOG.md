# Changelog

<!--next-version-placeholder-->

## v2.0.2 (31/03/2023)

### Fix

- Fixed video parsing function, which previously raised a KeyError when videos didn't have 'tags' or 'defaultAudioLanguage' attributes.

## v2.0.1 (20/03/2023)

### Documentation

- Changed docstring style to Google
- API reference now included in Readthedocs

## v2.0.0 (16/03/2023)

### Feature

- `youte hydrate` is now broken down to `youte videos` and `youte channels`
- `youte get-comments` is now `youte comments` and `youte replies`
- `youte most-popular` is now `youte chart`
- `youte get-related` is now `youte related-to`
- Resuming search is no longer available. Instead, you can set a limit on the number of search pages returned.
- All youte commands that retrieve data from YouTube API now won't print results to the shell, but store them in a specified json or jsonl file. This is to avoid clogging up the shell.
- Tidying to an SQlite (`youte tidy`) database is temporarily removed

### Documentation

- Better docstrings included in all client-facing functions

## v1.3.0 (24/02/2023)

### Feature

- `youte search` can now resume without inputting params
- added region and language filter to `youte search`

### Fix

- Clearer error messaging when getting API key

## v1.2.0

### Feature

- Add the option to limit search result pages
- `youte tidy` can now process multiple JSON at once

## v1.1.0

### Feature:

- `most-popular`: retrieves most top videos in a region or category
- `get-related`: retrieves videos related to a specified video
- `youte config add-key` now checks for duplicate API key.

## v1.0.0

### Feature:

- A working version that use _search_, _comment_, _commentThread_, _video_, and _channel_ endpoints:
- Search function with basic parameters
- Hydrate video, channel, and comment data
- Tidy output into csv and SQLite database
