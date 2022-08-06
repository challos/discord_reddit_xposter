from .local_cache import LocalCache
from .rest_cache import RESTCache


class Cache:
    """
    Factory for caches. There are several types of caches:

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
            return LocalCache(localcache_db_filename, username)

        if username and password and url:
            return RESTCache(username, password, url)

        print("Error, check arguments passed to the Cache")
        return None
