#!/usr/bin/env python3

from asyncio import sleep
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
    def __init__(
        self, cache_filename: str, webhook_urls: list, username: str, avatar_url: str
    ):
        """Initializes cross poster object.

        Args:
            cache_filename (str): filename of the cache
            webhook_urls (list): a list of the webhook urls to use
            username (str): the username the bot should use
            avatar_url (str): the url of the avatar the bot should use
        """
        self.cache: dict = {}
        self.avatar_url = avatar_url
        self.username = username
        self.webhook_urls = webhook_urls
        self.cache_filename = cache_filename
        self.load_cache(self.cache_filename)

    def load_cache(self, filename: str):
        """
        Loads the cache from a file into memory (self.cache)

        Args:
            filename (str): the filename to be read from
        """
        if not os.path.exists(filename):
            with open(filename, "w") as fp:
                pass
            return

        with open(filename, "r") as fp:
            for line in fp:
                line = line.strip()
                self.cache[line] = ""

    def update_cache(self, id: str):
        """
        Updates both the in memory cache, and this object's given cache filename.

        Args:
            id (str): the id of the post to update the cache with
        """
        if not os.path.exists(self.cache_filename):
            with open(self.cache_filename, "w") as fp:
                pass

        # no dupe
        if id in self.cache:
            return

        with open(self.cache_filename, "a+") as fp:
            fp.write(id + "\n")

        self.cache[id] = ""
        print("Cache updated with id: ", id)

    def post_submission(self, submission, reddit_config_url: str):
        """
        Posts a submission from PRAW to all webhook urls this crossposter has.

        Args:
            submission (submission): the reddit submission to be cross posted to discord.
            reddit_config_url (str): the reddit url to be used, should be from the PRAW reddit object.
        """
        with requests.Session() as session:
            for webhook_url in self.webhook_urls:
                webhook = SyncWebhook.from_url(
                    webhook_url,
                    session=session,
                )

                submission_url = reddit_config_url + submission.permalink
                post_url = submission.url
                if (
                    "crosspost_parent" in vars(submission)
                    and not r"redd.it" in submission.url
                    and not r"http" in submission.url
                ):
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


def main(
    reddit: praw.Reddit,
    x_poster: CrossPoster,
    subreddit_name: str,
    post_limit: int,
    wait_period: int,
):
    """
    Main function.

    Args:
        reddit (praw.Reddit): reddit object from praw to use for submissions
        x_poster (CrossPoster): cross poster object to use for cross posting to Discord
        subreddit_name (str): the name of the subreddit to cross post to
        post_limit (int): how many posts can be gathered from one call of subreddit.new
        wait_period (int): how many minutes should pass before the post is cross posted (usually to prevent spam)

    Returns:
        CrossPoster: returns the possibly changed cross poster object
    """
    subreddit = reddit.subreddit(subreddit_name)
    # get in reverse order to post oldest to newest
    submissions = [submission for submission in subreddit.new(limit=post_limit)][::-1]
    for submission in submissions:
        if not submission.removal_reason and submission.id not in x_poster.cache:
            time_passed = int(
                (datetime.timestamp(datetime.now()) - submission.created_utc) / 60
            )
            if wait_period > 5:
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
    x_poster = CrossPoster(
        CACHE_FILE,
        webhook_urls,
        config["xposter"]["username"],
        config["xposter"]["avatar"],
    )
    subreddit_name = config["xposter"]["subreddit"]
    
    post_limit = int(config["xposter"]["post_limit"])
    #wait period is in minutes
    wait_period = int(config["xposter"]["wait_period"])
    #sleep time is in minutes
    sleep_time = int(config["xposter"]["sleep_time"])
    prev_cache_count = 0
    while True:
        num_files = len(x_poster.cache) - prev_cache_count
        if num_files > 0:
            print("RAN AT: ", datetime.now())
            print("NUMBER OF FILES LOADED: ", num_files)

        prev_cache_count = len(x_poster.cache)
        x_poster = main(reddit, x_poster, subreddit_name, post_limit, wait_period)
        time.sleep(sleep_time * 60)
