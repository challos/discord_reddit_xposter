#!/usr/bin/env python3

import configparser
import time
from datetime import datetime

from cache import Cache
from cross_poster import CrossPoster
from subreddit_post_gatherer import SubredditPostGatherer

CONFIG_FILE = "xposter.ini"
import praw


def main():
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    webhook_urls = [
        webhook_url.strip()
        for webhook_url in config["xposter"]["webhook_urls"].split(",")
    ]
    reddit = praw.Reddit("xpost_bot", user_agent="xpost_bot v0.1")
    cache = Cache(**config["cache"])

    cross_poster = CrossPoster(
        cache=cache,
        webhook_urls=webhook_urls,
        username=config["xposter"]["username"],
        avatar_url=config["xposter"]["avatar"],
        reddit_config_url=reddit.config.reddit_url,
    )
    subreddit_gatherer = SubredditPostGatherer(
        reddit,
        config["xposter"]["subreddit"],
        int(config["xposter"]["post_limit"]),
    )
    while True:
        posts = subreddit_gatherer.posts(int(config["xposter"]["wait_period"]))
        good_posts = cross_poster.cache.check_posts(posts)
        print(
            "Checked posts at: {} and found {} good posts.".format(
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"), len(good_posts)
            )
        )

        for submission in good_posts:
            cross_poster.post_submission(submission)
        time.sleep(int(config["xposter"]["sleep_time"]) * 60)


if __name__ == "__main__":
    main()
