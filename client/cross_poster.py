from cache import Cache
import requests
from discord import SyncWebhook


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
        """
        An object for crossposting Reddit posts to Discord.

        Parameters
        ----------
        cache : Cache
            The cache to use for checking whether or not a post has already been posted
            to Discord.
        webhook_urls : list
            A list of webhook urls to use for posting.
        username : str
            The username to use when posting to Discord.
        avatar_url : str
            The URL for the avatar to use for the user when posting to Discord.
        reddit_config_url : str
            What URL to use for Reddit.
        """
        self.cache = cache
        self.avatar_url = avatar_url
        self.username = username
        self.webhook_urls = webhook_urls
        self.reddit_config_url = reddit_config_url
        """

        Args:
            submission (submission): 
        """

    def post_submission(self, submission):
        """
        Posts a submission from PRAW to all webhook urls this crossposter has.

        Parameters
        ----------
        submission : Any
            The Reddit submission to be posted to Discord.
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
                success = self.cache.add_post(submission)
                if not success:
                    print(
                        "Already exists: User: {} Subreddit: {} Post_id: {}".format(
                            self.cache.username,
                            submission.subreddit.display_name,
                            submission.id,
                        )
                    )
