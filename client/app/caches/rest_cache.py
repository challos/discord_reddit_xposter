from .base_cache import BaseCache
from functools import wraps
from urllib.parse import urljoin
import requests


class RESTCache(BaseCache):
    """
    Cache variant where whether or not posts have been crossposted is stored externally,
    and checked/updated with REST.

    Parameters
    ----------
    Cache : MetaClass
        The meta class for caches.
    """

    def __init__(self, username: str, password: str, url: str):
        self.username = username
        self.password = password
        self.url = url
        self.token_header = None

    def need_token(f):
        """
        A decorator for when certain actions require a token. Sets self.header_token to
        the necessary token, and sets it to none after the function is complete.

        Parameters
        ----------
        f : Callable
            The function to wrap.


        Returns
        -------
        Wrapped Callable
            A wrapped version of the function.
        """

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
        return not resp.json()["exists"]

    def add_posts(self, submission):
        pass
