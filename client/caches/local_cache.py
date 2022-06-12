from .base_cache import BaseCache
import base
import sqlalchemy
from sqlalchemy.orm import sessionmaker
from client_post import ClientPost


class LocalCache(BaseCache):
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
