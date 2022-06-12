from abc import ABC, abstractmethod
from functools import wraps
import requests
from urllib.parse import urljoin
from client_post import ClientPost
import sqlalchemy
from sqlalchemy import MetaData
from sqlalchemy.orm import sessionmaker, scoped_session
import base


class Cache(ABC):
    """
    Metaclass for caches. There are several types of caches:

    A RESTCache, where posts are stored possibly elsewhere, on a server running the main
    app in the server directory. Requires a username and password for the user, and a
    url that the server is at.

    A LocalCache, where posts are stored in a db file, locally. Requires the username
    and the filename of the .db file to use as a cache.

    Parameters
    ----------
    localcache_db_filename : str
        The filename of the .db file to be used for the LocalCache.
    username : str
        The username to use for the RESTCache and the LocalCache.
    password : str
        The password to use for the RESTCache.
    url : str
        The url to use for the RESTCache.

    """

    def __new__(
        cls,
        localcache_db_filename: str = "",
        username: str = "",
        password: str = "",
        url: str = "",
    ):
        if localcache_db_filename:
            obj = object.__new__(LocalCache)
            return obj

        if username and password and url:
            obj = object.__new__(RESTCache)
            return obj

        print("Error, check arguments passed to the Cache")
        return None

    @abstractmethod
    def check_post(self, user: str, submission):
        """
        Checks if a post is in the cache.

        Parameters
        ----------
        submission : Any
            The submission to be checked for whether or not it's in the cache.
        """
        pass

    @abstractmethod
    def check_posts(self, submissions: list) -> list:
        """
        Checks if multiple submissions are in the cache, and returns only the
        submissions that are not in the cache.

        Parameters
        ----------
        submissions : list
            A list of the submissions to check for whether or not they're in the cache.

        Returns
        -------
        list
            A list of the submissions from those initially given that are not in the
            cache.

        """
        pass

    @abstractmethod
    def add_post(self, submission) -> bool:
        """
        Adds a submission to the cache.

        Parameters
        ----------
        submission : Any
            The submission to add the cache.

        Returns
        -------
        bool
            True if the submission was successfully added, False otherwise.
        """
        pass

    @abstractmethod
    def add_posts(self, submissions):
        """
        Adds multiple posts to the cache.

        Parameters
        ----------
        submissions : list
            The submissions to add to the cache.
        """
        pass


class LocalCache(Cache):
    """
    Cache variant where whether or not posts have been crossposted is stored locally.

    Parameters
    ----------
    Cache : MetaClass
        The meta class for caches.
    """

    def __init__(self, localcache_db_filename: str, username: str):
        self.db_filename = localcache_db_filename
        self.username = username
        self.cache = {}
        engine = sqlalchemy.create_engine("sqlite:///" + localcache_db_filename)
        base.Base.metadata.create_all(engine, checkfirst=True)
        Session = sessionmaker(bind=engine)
        self.session = Session()

    def check_post(self, submission):
        post = (
            self.session.query(ClientPost)
            .filter_by(
                username=self.username,
                subreddit=submission.subreddit.display_name,
                post_id=submission.id,
            )
            .first()
        )
        if post:
            return True

        return False

    def check_posts(self, submissions: list):
        result = []
        for submission in submissions:
            if not self.check_post(submission):
                result.append(submission)

        return result

    def add_post(self, submission):
        if not self.check_post(submission):
            self.session.add(
                ClientPost(
                    self.username, submission.subreddit.display_name, submission.id
                )
            )
            self.session.commit()
            return True

        return False

    def add_posts(self, submissions: list):
        for submission in submissions:
            self.add_post(submission)


class RESTCache(Cache):
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
