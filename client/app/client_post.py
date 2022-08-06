from sqlalchemy import Column, Integer, String, MetaData
from base import Base


class ClientPost(Base):
    """
    Represents a post in the cache.

    Parameters
    ----------
    Base : DeclarativeBase
        The declarative base to use the client in.
    """

    __tablename__ = "posts"
    id = Column(Integer, primary_key=True)
    username = Column(String(255), nullable=False)
    subreddit = Column(String(255), nullable=False)
    post_id = Column(String(255), nullable=False)

    def __init__(self, username: str, subreddit: str, post_id: str):
        self.username = username
        self.subreddit = subreddit
        self.post_id = post_id
