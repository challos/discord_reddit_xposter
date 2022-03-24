#!/usr/bin/env python3

import praw
import prawcore
from discord import SyncWebhook
import os
import requests
from datetime import datetime
import time
import configparser

CONFIG_FILE = "xposter.ini"
CACHE_FILE = "cache.txt"


class CrossPoster:
    def __init__(self, filename: str, webhook_urls: list, username: str, avatar_url: str):
        self.cache: dict = {}
        self.avatar_url = avatar_url
        self.username = username
        self.webhook_urls = webhook_urls
        self.filename = filename
        self.load_cache(self.filename)

    def load_cache(self, filename: str):
        if not os.path.exists(filename):
            with open(filename, "w") as fp:
                pass
            return

        with open(filename, "r") as fp:
            for line in fp:
                line = line.strip()
                self.cache[line] = ""

    def update_cache(self, id: str):
        if not os.path.exists(self.filename):
            with open(self.filename, "w") as fp:
                pass

        # no dupe
        if id in self.cache:
            return

        with open(self.filename, "a+") as fp:
            fp.write(id + "\n")

        self.cache[id] = ""
        print("Cache updated with id: ", id)

    def post_submission(self, submission, reddit_config_url: str):
        with requests.Session() as session:
            for webhook_url in self.webhook_urls:
                webhook = SyncWebhook.from_url(
                    webhook_url,
                    session=session,
                )

                submission_url = reddit_config_url + submission.permalink
                post_url = submission.url
                if "crosspost_parent" in vars(submission) and not r'redd.it' in submission.url and not r'http' in submission.url:
                    print("CROSSPOSTED!")
                    post_url = reddit_config_url + submission.url
                
                if submission_url == post_url:
                    post_url = ""

                webhook_message = "{} by {}:\n{}\n{}".format(
                    submission.title,
                    submission.author,
                    submission_url,
                    post_url,
                )
                webhook.send(
                    webhook_message,
                    username=self.username,
                    avatar_url=self.avatar_url,
                )
                # if there's a runtime error, this update should only happen afterwards.
                self.update_cache(submission.id)


def main(reddit: praw.Reddit, x_poster: CrossPoster, subreddit_name: str, post_limit: int):
    subreddit = reddit.subreddit(subreddit_name)
    # get in reverse order to post oldest to newest
    submissions = [submission for submission in subreddit.new(limit=post_limit)][::-1]
    for submission in submissions:
        if not submission.removal_reason and submission.id not in x_poster.cache:
            time_passed = int(
                (datetime.timestamp(datetime.now()) - submission.created_utc) / 60
            )
            if time_passed > 5:
                try:
                    x_poster.post_submission(submission, reddit.config.reddit_url)
                except RuntimeError as e:
                    print("Error, trying again in a bit...")
                    break
                except prawcore.exceptions.ServerError as e:
                    print("Server Error...")
                    break
                except prawcore.exceptions.RequestException as e:
                    print("Too many retries...")
                    break

    # pointers aren't a thing rip
    return x_poster


if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    webhook_urls = [
        webhook_url.strip()
        for webhook_url in config["xposter"]["webhook_urls"].split(",")
    ]
    reddit = praw.Reddit("xpost_bot", user_agent="xpost_bot v0.1")
    x_poster = CrossPoster(CACHE_FILE, webhook_urls, config["xposter"]["username"], config["xposter"]["avatar"])
    subreddit_name = config["xposter"]["subreddit"]
    post_limit = int(config["xposter"]["post_limit"])
    prev_cache_count = 0
    while True:
        num_files = len(x_poster.cache) - prev_cache_count
        if num_files > 0:
            print("RAN AT: ", datetime.now())
            print("NUMBER OF FILES LOADED: ", num_files)

        prev_cache_count = len(x_poster.cache)
        x_poster = main(reddit, x_poster, subreddit_name, post_limit)
        # 3 minutes * 60 for 180 seconds
        time.sleep(3 * 60)
