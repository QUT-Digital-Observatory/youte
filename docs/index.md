---
title: "youte"
---

`youte` is a command-line tool that collects and tidies YouTube video metadata and comments from YouTube Data API v.3. At the moment, the tool supports collecting public data that does not require OAuth 2.0.

`youte` can collect the following data:

- search results
- video metadata
- channel metadata
- comment threads and comments

It does so while handling pagination and YouTube API's rate limits. `youte` also provides the functionality to tidy raw JSON data into tabular format, either in a CSV file or an SQLite database.

## Installing `youte`

If you have Python 3.8 and above installed, you can install `youte` with `pip`.

```shell
python -m pip install youte
```

If you run into issues, first try upgrading `pip`, `setuptools`, and `wheel`.

```shell
python -m pip install --upgrade pip setuptools wheel
```

## Rate limit and YouTube API Quota system

Most often, there is a limit to how many requests you can make to YouTube API per day. YouTube Data API uses a quota system, whereby each request, valid or invalid, incurs a quota cost of at least one point. Different endpoints will use up different quota costs. For example:

- search endpoint costs 100 units per request
- video, channel, commentThread, and comment endpoints each costs 1 unit per request

Refer to [YouTube Data API's documentation](https://developers.google.com/youtube/v3/determine_quota_cost) for more details on the costs of each endpoint.

Free accounts get an API quota cap of 10,000 units per project per day, which resets at midnight Pacific Time. You can complete an [Audit and Quota Extension form](https://developers.google.com/youtube/v3/guides/quota_and_compliance_audits) to request additional quota on top of your default allocation.

At present, you can only check your quota usage on the Quotas page in the API Console. It is not possible to monitor quota usage via metadata returned in the API response.

`youte` does not monitor quota usage. However, it handles errors when quota is exceeded by sleeping until quota reset time.

## Data governance considerations

Activities involving data collected from YouTube Data API (e.g. collecting, analysing, storing, sharing, and archiving) should be in accordance with [YouTube API Terms of Service](https://developers.google.com/youtube/terms/api-services-terms-of-service) and [Developer Policies](https://developers.google.com/youtube/terms/developer-policies).

At the same time, it is best-practice data governance to consider data implications that might arise from using YouTube data. Refer to [this guide](https://www.digitalobservatory.net.au/data-governance-guide/) for a high-level list of data governance considerations.

## Other tools

Google provides client libraries to interact with their APIs, including YouTube Data API: [https://developers.google.com/youtube/v3/libraries](https://developers.google.com/youtube/v3/libraries). The libraries are available in a number of programming languages such as Java, Python, and JavaScript.

## Feedback is welcome!

`youte` is still in its infancy, and we are working to improve and expand its capabilities. Let us know your feedback or suggestions by creating GitHub issues or emailing us at [digitalobservatory@qut.edu.au](mailto:digitalobservatory@qut.edu.au).
