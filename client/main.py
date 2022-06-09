#!/usr/bin/env python3

import praw
import prawcore
from discord import SyncWebhook
from urllib.parse import urljoin
import requests
from datetime import datetime
import time
import configparser
from functools import wraps

from abc import ABC, abstractmethod

CONFIG_FILE = "xposter.ini"


class Cache(ABC):
    @abstractmethod
    def check_post(self, *args, **kwargs):
        pass

    @abstractmethod
    def check_posts(self, *args, **kwargs):
        pass

    @abstractmethod
    def load_cache(self, *args, **kwargs):
        pass

    @abstractmethod
    def update_cache(self, *args, **kwargs):
        pass

    @abstractmethod
    def add_post(self, *args, **kwargs):
        pass


# class RESTCache(Cache):
class RESTCache:
    def __init__(self, username: str, password: str, url: str):
        # TODO implement clientside in memory cache
        self.username = username
        self.password = password
        self.url = url
        self.token_header = None

    def need_token(f):
        @wraps(f)
        def decorator(self, *args, **kwargs):
            login_url = urljoin(self.url, "users/login")
            resp = requests.get(login_url, auth=(self.username, self.password))
            if resp.status_code > 299:
                print("Error with logging in!")
                exit()

            token = resp.json()["token"]
            self.token_header = {"Authorization": "Bearer {}".format(token)}
            func = f(self, *args, **kwargs)
            # unset so it is retrieved again
            self.token_header = None
            return func

        return decorator

    @need_token
    def check_posts(self, submissions: list):
        contains_url = urljoin(self.url, "posts/")
        posts = []
        for submission in submissions:
            posts.append(
                {
                    "subreddit": submission.subreddit.display_name,
                    "post_id": submission.id,
                }
            )
        posts_dict = {"posts": posts}

        resp = requests.get(contains_url, headers=self.token_header, json=posts_dict)

        good_posts = []
        for post in resp.json()["posts"]:
            if not post["exists"]:
                for submission in submissions:
                    if (
                        submission.id == post["post_id"]
                        and submission.subreddit.display_name == post["subreddit"]
                    ):

                        good_posts.append(submission)
                        break

        return good_posts

    @need_token
    def check_post(self, submission):
        contains_url = urljoin(self.url, "posts/")
        post_dict = {
            "post": {
                "subreddit": submission.subreddit.display_name,
                "post_id": submission.id,
            }
        }
        resp = requests.get(contains_url, headers=self.token_header, json=post_dict)
        return resp.json()["exists"]

    @need_token
    def add_post(self, submission):
        add_url = urljoin(self.url, "posts/")
        post_dict = {
            "post": {
                "subreddit": submission.subreddit.display_name,
                "post_id": submission.id,
            }
        }
        resp = requests.post(add_url, headers=self.token_header, json=post_dict)
        return resp.json()["exists"]


class CrossPoster:
    def __init__(
        self,
        *,
        cache: Cache,
        webhook_urls: list,
        username: str,
        avatar_url: str,
        reddit_config_url: str
    ):
        """Initializes cross poster object.

        Args:
            cache_filename (str): filename of the cache
            webhook_urls (list): a list of the webhook urls to use
            username (str): the username the bot should use
            avatar_url (str): the url of the avatar the bot should use
        """
        self.cache = cache
        self.avatar_url = avatar_url
        self.username = username
        self.webhook_urls = webhook_urls
        self.reddit_config_url = reddit_config_url

    def post_submission(self, submission):
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

                submission_url = self.reddit_config_url + submission.permalink
                post_url = submission.url
                if (
                    "crosspost_parent" in vars(submission)
                    and not r"redd.it" in submission.url
                    and not r"http" in submission.url
                ):
                    print("CROSSPOSTED!")
                    post_url = self.reddit_config_url + submission.url

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
                print(
                    "Already exists:",
                    self.cache.add_post(submission),
                )


class SubredditGatherer:
    def __init__(self, subreddit_name: str, post_limit: int, wait_period: int):
        self.subreddit = reddit.subreddit(subreddit_name)
        self.post_limit = post_limit
        self.wait_period = wait_period

    def get_posts(self):
        # get in reverse order to post oldest to newest
        result = []
        try:
            submissions = [
                submission for submission in self.subreddit.new(limit=self.post_limit)
            ][::-1]
            for submission in submissions:
                if not submission.removal_reason:
                    time_passed = int(
                        (datetime.timestamp(datetime.now()) - submission.created_utc)
                        / 60
                    )
                    if time_passed > self.wait_period:
                        result.append(submission)
        except RuntimeError:
            print("Error, trying again in a bit...")
        except prawcore.exceptions.RequestException:
            print("Too many retries...")
            # just restart the loop, will probably fix itself
        except prawcore.exceptions.ServerError:
            print("Server error...")

        return result


if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    webhook_urls = [
        webhook_url.strip()
        for webhook_url in config["xposter"]["webhook_urls"].split(",")
    ]
    reddit = praw.Reddit("xpost_bot", user_agent="xpost_bot v0.1")
    cache = None
    if (
        "username" in config["cache"]
        and "password" in config["cache"]
        and "url" in config["cache"]
    ):
        cache = RESTCache(
            config["cache"]["username"],
            config["cache"]["password"],
            config["cache"]["url"],
        )
    else:
        print("Error with config file.")
        exit()

    cross_poster = CrossPoster(
        cache=cache,
        webhook_urls=webhook_urls,
        username=config["xposter"]["username"],
        avatar_url=config["xposter"]["avatar"],
        reddit_config_url=reddit.config.reddit_url,
    )
    temp = SubredditGatherer(
        config["xposter"]["subreddit"],
        int(config["xposter"]["post_limit"]),
        # wait period is in minutes
        int(config["xposter"]["wait_period"]),
    )
    while True:
        posts = temp.get_posts()
        good_submissions = cross_poster.cache.check_posts(posts)

        for submission in good_submissions:
            cross_poster.post_submission(submission)
        time.sleep(int(config["xposter"]["sleep_time"]) * 60)
