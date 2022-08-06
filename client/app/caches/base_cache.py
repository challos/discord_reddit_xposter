from abc import ABC, abstractmethod

class BaseCache(ABC):
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