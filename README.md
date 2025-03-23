# Video Data Scraper

## Overview
This script is an asynchronous video data scraper designed to fetch video details from an API endpoint. It efficiently handles rate limits using exponential backoff and maintains progress tracking for interrupted runs.

## Features
- Uses `aiohttp` for asynchronous requests.
- Implements **exponential backoff** for rate limiting.
- Supports **progress tracking and resumption** in case of failures or interruptions.
- Uses **randomized user-agents** to avoid detection.
- Saves fetched data incrementally to prevent data loss.
- Handles **429 rate limit errors** and retries failed requests.

## Dependencies
Ensure you have Python 3.7+ installed and install dependencies via:
```sh
pip install aiohttp
```

## Configuration
Modify the following parameters in the script before running:

- **API Endpoint:** `url` → Set to the backend API path.
- **Save Path:** `save_path` → Path to store collected video data.
- **Progress Path:** `progress_path` → Path to track progress.
- **Total Video IDs:** `TOTAL_IDS` → Number of videos to process.
- **Concurrency:** `MAX_CONCURRENT_REQUESTS` → Number of concurrent requests.
- **Delays:** `MIN_DELAY`, `MAX_DELAY` → Random delays between requests.
- **Exponential Backoff:** `EXPONENTIAL_BACKOFF_START`, `EXPONENTIAL_BACKOFF_FACTOR`, `MAX_BACKOFF`.
- **User Agents:** `ROTATING_USER_AGENTS` → List of User-Agent strings for randomization.

## How It Works
1. **Initial Setup**
   - Reads progress from `progress_path`.
   - Loads previously saved data if available.
   - Applies a cooldown if the last run was recent.

2. **Fetching Video Data**
   - Makes `POST` requests with randomized headers.
   - Handles API errors and retries failed requests.
   - Implements **exponential backoff** for rate limits.

3. **Saving Progress**
   - Saves fetched data every `SAVE_EVERY` successful requests.
   - Stores failed requests separately for future retries.
   - Progress file ensures resumption from the last processed ID.

4. **Completion Metrics**
   - Logs fetched videos and failed ones.
   - Displays processing rate (requests per minute).

## Running the Script
Run the script using:
```sh
python script.py
```

To stop and resume later, use `CTRL+C`. Progress will be saved automatically.

## Logs
All logs are stored in `scraper.log` and include:
- Successfully fetched video names.
- Rate limit warnings and applied backoff.
- Errors with HTTP response codes.

## Customization
- Modify the `fetch_video` function to adjust request structure.
- Extend logging for more detailed tracking.
- Change `ROTATING_USER_AGENTS` to add more user agents.

## Troubleshooting
- **Script crashes unexpectedly?** Restart, and it will resume from the last saved ID.
- **Rate-limited frequently?** Increase `EXPONENTIAL_BACKOFF_START` or reduce `MAX_CONCURRENT_REQUESTS`.
- **Data file corrupted?** Delete `progress_path` and restart fresh.

## Disclaimer
This script is provided as-is. Ensure compliance with the target API's terms of service before use.

