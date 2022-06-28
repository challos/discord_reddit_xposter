import praw
import prawcore
from datetime import datetime


class SubredditPostGatherer:
    """
    Gathers posts from a given subreddit.
    """

    def __init__(
        self,
        reddit: praw.Reddit,
        subreddit_name: str,
        post_limit: int,
    ):
        """
        Initializer for SubredditPostGatherer.

        Parameters
        ----------
        reddit : praw.Reddit
            The reddit object to use and retrieve a subreddit object from.
        subreddit_name : str
            The name of the subreddit to gather posts from.
        post_limit : int
            The maximum number of posts to retrieve from the subreddit at a given time.
        """
        self.subreddit = reddit.subreddit(subreddit_name)
        self.post_limit = post_limit

    def posts(self, wait_period: int) -> list:
        """
        Retrieves posts from this subreddit, with a given wait period.

        Parameters
        ----------
        list
            Returns a list of submissions that were both not removed by a mod, and also
            past the set wait period

        wait_period : int
            Required 'age' of post (in minutes) to be considered valid. Intended so that
            spam bots which are removed after a few minutes are effectively 'ignored'.

        Returns
        -------
        """
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
                    if time_passed > wait_period:
                        result.append(submission)
        except RuntimeError:
            print("Error, trying again in a bit...")
        except prawcore.exceptions.RequestException:
            print("Too many retries...")
            # just restart the loop, will probably fix itself
        except prawcore.exceptions.ServerError:
            print("Server error...")
        except prawcore.exceptions.ResponseException:
            print("Reponse exception...")

        return result
