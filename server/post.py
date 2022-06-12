from typing import Union
from flask import (
    request,
    jsonify,
    make_response,
    Blueprint,
    current_app,
)

from user import token_required, User

posts_page = Blueprint("posts_page", __name__)

with current_app.app_context():
    db = current_app.config["database"]


class Post(db.Model):
    """
    Object that represents a post made on Discord.

    Parameters
    ----------
    db : Any
        A database connection.
    """

    __tablename__ = "posts"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(255), nullable=False)
    subreddit = db.Column(db.String(255), nullable=False)
    post_id = db.Column(db.String(255), nullable=False)

    def __init__(self, username: str, subreddit: str, post_id: str):
        self.username = username
        self.subreddit = subreddit
        self.post_id = post_id

    def to_dict(self):
        json_dict = {}
        json_dict["username"] = self.username
        json_dict["subreddit"] = self.subreddit
        json_dict["post_id"] = self.post_id

        return json_dict

    @classmethod
    def jsonify_query(cls, query: list["Post"]):
        """
        Jsonify's a query

        Parameters
        ----------
        query : _type_
            _description_

        Returns
        -------
        _type_
            _description_
        """
        result = {"posts": []}
        for post in query:
            result["posts"].append(post.to_dict())

        return jsonify(result)

    @classmethod
    def get_subreddit_posts(cls, username: str, subreddit: str):
        """
        Retrieves posts for a specific user for a specific subreddit.

        Parameters
        ----------
        username : str
            User's username.
        subreddit : str
            Subreddit to be checked.

        Returns
        -------
        Response
            Jsonified query response.
        """
        return cls.jsonify_query(
            cls.query.filter_by(username=username, subreddit=subreddit)
        )

    @classmethod
    def add_post(cls, username: str, subreddit: str, post_id: str) -> dict:
        """
        Add a given post to the database.

        Parameters
        ----------
        username : str
            Username for the post.
        subreddit : str
            Subreddit for the post.
        post_id : str
            Post id for the post.

        Returns
        -------
        dict
            Returns a dict, which contains the original post information as well as the
            'exists' keyword for whether or not the post existed before being added.
        """
        post = Post.query.filter_by(
            username=username, subreddit=subreddit, post_id=post_id
        ).first()
        post_dict = dict(username=username, subreddit=subreddit, post_id=post_id)
        if post:
            post_dict["exists"] = True
            return post_dict

        post: Post = db.session.add(
            cls(username=username, subreddit=subreddit, post_id=post_id)
        )
        db.session.commit()
        post_dict["exists"] = False
        return post_dict

    @classmethod
    def add_posts(
        cls,
        username: str,
        posts: list[dict[str, str]],
    ) -> list[dict]:
        """
        Adds multiple posts to the database.

        Parameters
        ----------
        username : str
            Username to use for the posts.
        posts : list[dict[str, str]]
            A list of posts, which should contain the 'subreddit' and 'post_id' keyword.

        Returns
        -------
        list[dict]
            A list of subreddit posts that were successfully added.
        """
        result = []
        for thing in posts:
            result.append(cls.add_post(username, thing["subreddit"], thing["post_id"]))

        return result

    # should be used as a helper function
    @classmethod
    def check_post(cls, username: str, subreddit: str, post_id: str) -> dict:
        """
        Checks whether or not a post is already in the database.

        Parameters
        ----------
        username : str
            The username to check for.
        subreddit : str
            The subreddit to check for.
        post_id : str
            The post id to check for.

        Returns
        -------
        dict
            A dict with the original post information and the 'exists' keyword, which
            will be set to a boolean that is true if the post was already in the
            database, and false otherwise.
        """
        post: Post = cls.query.filter_by(
            username=username, subreddit=subreddit, post_id=post_id
        ).first()

        exists_flag = False
        if post:
            exists_flag = True

        return {
            "username": username,
            "subreddit": subreddit,
            "post_id": post_id,
            "exists": exists_flag,
        }

    @classmethod
    def check_posts(cls, username: str, posts: list[dict[str, str]]) -> list[dict]:
        """
        Checks whether or not several posts were already in the database.

        Parameters
        ----------
        username : str
            The username to check for.
        posts : list[dict[str, str]]
            The posts to check in the database for. Should have the 'subreddit' and
            'post_id' keyword.

        Returns
        -------
        list[dict]
            Returns a list of posts, with the 'exists' keyword, which will be set to a
            boolean that is true if the post was already in the database and false
            otherwise.
        """
        result = []
        for post in posts:
            post_dict = cls.check_post(username, post["subreddit"], post["post_id"])

            result.append(post_dict)

        return result


@posts_page.get("/")
@token_required
def check_multiple_posts(current_user: User):
    """
    Check multiple posts using JSON.

    Parameters
    ----------
    current_user : User
        The current user.

    Returns
    -------
    response
        A response either with JSON containing the desired posts, or an error.
    """
    if not request.is_json:
        return Post.jsonify_query(Post.query.filter_by(username=current_user.username))

    data = request.get_json()

    if "posts" in data:
        posts = data["posts"]
        if not isinstance(posts, list):
            return make_response("Error, posts needs to be a list.", 415)

        checked_posts = Post.check_posts(current_user.username, posts)

        return jsonify({"posts": checked_posts}), 200

    if "post" in data:
        post = data["post"]
        if not isinstance(post, dict):
            return make_response("Error, post needs to be a dict.", 415)

        checked_post = Post.check_post(
            current_user.username, post["subreddit"], post["post_id"]
        )
        return jsonify(checked_post), 200

    return make_response("Error, need a posts list or post object.", 415)


@posts_page.get("/<subreddit>")
@token_required
def check_subreddit(current_user: User, subreddit: str):
    """
    Checks what posts are in a given subreddit.

    Parameters
    ----------
    current_user : User
        The current user.
    subreddit : str
        The subreddit to check for posts.

    Returns
    -------
    Response
        The JSON for all the posts found on that subreddit.
    """
    posts = Post.query.filter_by(username=current_user.username, subreddit=subreddit)
    return Post.jsonify_query(posts), 200


@posts_page.post("/")
@token_required
def add_subreddit_posts(current_user: User):
    """
    Adds posts to a subreddit.

    Parameters
    ----------
    current_user : User
        The current user.

    Returns
    -------
    Response
        JSON with the result of adding the posts, or an error.
    """
    if not request.is_json:
        return make_response("Request must be in JSON.", 415)

    data = request.get_json()

    if "posts" in data:
        posts = data["posts"]
        if not isinstance(posts, list):
            return make_response("Error, posts needs to be a list.", 415)

        result = Post.add_posts(current_user.username, posts)

        return jsonify(result), 200

    if "post" in data:
        post = data["post"]
        if not isinstance(post, dict):
            return make_response("Error, post needs to be a dict.", 415)

        checked_post = Post.add_post(
            current_user.username, post["subreddit"], post["post_id"]
        )
        return jsonify(checked_post), 200

    return make_response("Error, need a posts list or post object.", 415)
