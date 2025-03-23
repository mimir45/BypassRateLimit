import aiohttp
import asyncio
import random
import json
import os
import time
from aiohttp import ClientConnectorError, ClientResponseError
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("video_scraper")

save_path = "path/to/save/"
progress_path = "path/to/progress/"
url = "url path to fetch data"

BATCH_SIZE = 8
MAX_CONCURRENT_REQUESTS = 2
MIN_DELAY = 1
MAX_DELAY = 3
EXPONENTIAL_BACKOFF_START = 30
EXPONENTIAL_BACKOFF_FACTOR = 2
MAX_BACKOFF = 60
TOTAL_IDS = 5169
SAVE_EVERY = 5
ROTATING_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:89.0) Gecko/20100101 Firefox/89.0"
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36"
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36"
    "Mozilla/5.0 (Linux; Android 10; Pixel 3 XL) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36"
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.190 Safari/537.36"
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Version/11.1 Safari/537.36"
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 "
    "Safari/537.36 Edge/80.0.361.66"
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:93.0) Gecko/20100101 Firefox/93.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1"
]
def get_headers():

    user_agent = random.choice(ROTATING_USER_AGENTS)
    return {
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        #modify referer and origin
        "Referer": "back end api path",
        "User-Agent": user_agent,
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "en-US,en;q=0.9",
        "Origin": "url",
        "DNT": "1",
        "Connection": "keep-alive",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "X-Requested-With": "XMLHttpRequest",
    }


async def fetch_video(session, video_id, backoff_time=EXPONENTIAL_BACKOFF_START):
    headers = get_headers()
    try:
        await asyncio.sleep(random.uniform(0.1, 0.5))

        async with session.post(
                url,
                headers=headers,
                data=f"id={video_id}",
                timeout=30,
                ssl=False
        ) as response:
            if response.status == 200:
                data = await response.json()
                if data.get("isError") is False and "name" in data:
                    logger.info(f"ID {video_id}: Successfully fetched '{data['name']}'")
                    return video_id, data["name"], None
                elif data.get("isError") is True and "rate" in data.get("message", "").lower():
                    logger.warning(f"ID {video_id}: Rate limited! Backing off for {backoff_time} seconds")
                    await asyncio.sleep(backoff_time)
                    next_backoff = min(backoff_time * EXPONENTIAL_BACKOFF_FACTOR, MAX_BACKOFF)
                    return await fetch_video(session, video_id, next_backoff)
                else:
                    error_msg = data.get("message", "API returned error")
                    logger.error(f"ID {video_id}: {error_msg}")
                    return video_id, None, error_msg
            elif response.status == 429:
                logger.warning(f"ID {video_id}: Rate limited (429)! Backing off for {backoff_time} seconds")
                await asyncio.sleep(backoff_time)
                next_backoff = min(backoff_time * EXPONENTIAL_BACKOFF_FACTOR, MAX_BACKOFF)
                return await fetch_video(session, video_id, next_backoff)
            else:
                logger.error(f"ID {video_id}: HTTP status {response.status}")
                return video_id, None, f"HTTP {response.status}"

    except (ClientConnectorError, ClientResponseError, asyncio.TimeoutError) as e:
        logger.error(f"ID {video_id}: Connection error - {str(e)}")
        await asyncio.sleep(min(5, backoff_time / 2))
        return await fetch_video(session, video_id, min(backoff_time * 1.5, MAX_BACKOFF))
    except Exception as e:
        logger.error(f"ID {video_id}: Unexpected error - {str(e)}")
        return video_id, None, str(e)


async def main():
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    progress_data = {
        "completed": {},
        "failed": {},
        "last_id": 0,
        "last_run": datetime.now().isoformat()
    }

    if os.path.exists(progress_path):
        try:
            with open(progress_path, "r", encoding="utf-8") as f:
                progress_data = json.load(f)
                logger.info(
                    f"Loaded progress: {len(progress_data['completed'])} completed, {len(progress_data['failed'])} failed")
                logger.info(f"Resuming from ID {progress_data['last_id']}")

                if "last_run" in progress_data:
                    try:
                        last_run = datetime.fromisoformat(progress_data["last_run"])
                        seconds_since_last_run = (datetime.now() - last_run).total_seconds()
                        if seconds_since_last_run < 300:
                            cooldown = random.uniform(30, 60)
                            logger.info(
                                f"Last run was only {seconds_since_last_run:.1f} seconds ago. Cooling down for {cooldown:.1f} seconds")
                            await asyncio.sleep(cooldown)
                    except (ValueError, TypeError):
                        pass
        except json.JSONDecodeError:
            logger.warning("Progress file is corrupted, starting fresh")

    if os.path.exists(save_path):
        try:
            with open(save_path, "r", encoding="utf-8") as f:
                video_data = json.load(f)
                logger.info(f"Loaded {len(video_data)} existing entries from main data file")
                for video_id, name in video_data.items():
                    progress_data["completed"][video_id] = name
        except json.JSONDecodeError:
            logger.warning("Data file is corrupted, but will use progress data if available")
            video_data = {id: name for id, name in progress_data["completed"].items()}
    else:
        video_data = {id: name for id, name in progress_data["completed"].items()}

    timeout = aiohttp.ClientTimeout(total=60, connect=30)

    connector = aiohttp.TCPConnector(
        limit=MAX_CONCURRENT_REQUESTS,
        limit_per_host=2,
        ssl=False,
        ttl_dns_cache=300,
        force_close=True,
    )

    session_kwargs = {
        "timeout": timeout,
        "connector": connector,
        "trust_env": True,
    }

    async with aiohttp.ClientSession(**session_kwargs) as session:
        start_id = progress_data["last_id"] + 1 if progress_data["last_id"] > 0 else 1
        success_since_save = 0

        queue = asyncio.Queue()

        remaining_ids = [id for id in range(start_id, TOTAL_IDS + 1)
                         if str(id) not in progress_data["completed"]]
        random.shuffle(remaining_ids)
        for vid_id in remaining_ids:
            await queue.put(vid_id)

        logger.info(f"Added {len(remaining_ids)} IDs to queue")

        start_time = time.time()
        processed_count = 0

        tasks = []
        for _ in range(MAX_CONCURRENT_REQUESTS):
            tasks.append(asyncio.create_task(process_queue(queue, session, video_data, progress_data)))

        await queue.join()

        for task in tasks:
            task.cancel()

        try:
            await asyncio.gather(*tasks, return_exceptions=True)
        except asyncio.CancelledError:
            pass

    end_time = time.time()
    elapsed = end_time - start_time
    rpm = processed_count / (elapsed / 60) if elapsed > 0 else 0

    progress_data["last_run"] = datetime.now().isoformat()
    with open(progress_path, "w", encoding="utf-8") as f:
        json.dump(progress_data, f, indent=4, ensure_ascii=False)

    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(video_data, f, indent=4, ensure_ascii=False)

    if progress_data["failed"]:
        failed_path = save_path.replace(".json", "_failed.json")
        with open(failed_path, "w", encoding="utf-8") as f:
            json.dump(progress_data["failed"], f, indent=4, ensure_ascii=False)
        logger.info(f"Failed IDs saved to {failed_path}")

    logger.info(f"✅ All videos saved to '{save_path}'")
    logger.info(f"Successfully fetched {len(video_data)} out of {TOTAL_IDS} videos")
    logger.info(f"Failed to fetch {len(progress_data['failed'])} videos")
    logger.info(f"Average request rate: {rpm:.2f} requests per minute")

# this  script writen  for collect video data u can modfy for anything
async def process_queue(queue, session, video_data, progress_data):
    success_since_save = 0
    processed_count = 0

    while True:
        try:
            video_id = await queue.get()

            str_id = str(video_id)
            if str_id in progress_data["completed"]:
                queue.task_done()
                continue

            vid_id, name, error = await fetch_video(session, video_id)
            processed_count += 1

            if name:
                video_data[str_id] = name
                progress_data["completed"][str_id] = name
                if str_id in progress_data["failed"]:
                    del progress_data["failed"][str_id]

                success_since_save += 1
                if success_since_save >= SAVE_EVERY:
                    progress_data["last_run"] = datetime.now().isoformat()
                    progress_data["last_id"] = max(progress_data["last_id"], video_id)
                    with open(progress_path, "w", encoding="utf-8") as f:
                        json.dump(progress_data, f, indent=4, ensure_ascii=False)
                    with open(save_path, "w", encoding="utf-8") as f:
                        json.dump(video_data, f, indent=4, ensure_ascii=False)
                    success_since_save = 0

                    completion_percentage = (len(progress_data["completed"]) / TOTAL_IDS) * 100
                    logger.info(
                        f"Progress: {len(progress_data['completed'])}/{TOTAL_IDS} ({completion_percentage:.1f}%)")
            elif error:
                progress_data["failed"][str_id] = error

            await asyncio.sleep(random.uniform(MIN_DELAY, MAX_DELAY))

            queue.task_done()

        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Worker error: {str(e)}")
            await asyncio.sleep(5)
            queue.task_done()


# Run async
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nScript interrupted by user. Progress has been saved.")
    except Exception as e:
        logger.error(f"Script crashed: {str(e)}")
        logger.info("You can resume from the last saved point.")