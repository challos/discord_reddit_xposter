from flask import (
    request,
    jsonify,
    make_response,
    Blueprint,
    current_app,
)

from users import token_required, User

posts_page = Blueprint("posts_page", __name__)

with current_app.app_context():
    db = current_app.config["database"]


class Post(db.Model):
    __tablename__ = "posts"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(255), nullable=False)
    subreddit = db.Column(db.String(255), nullable=False)
    post_id = db.Column(db.String(255), nullable=False, unique=True)

    def __init__(self, username: str, subreddit: str, post_id: str):
        self.username = username
        self.subreddit = subreddit
        self.post_id = post_id

    @classmethod
    def initialize(cls, username: str, subreddit: str, cache_txt_str: str):
        for line in open(cache_txt_str, "r"):
            db.session.add(
                cls(username=username, subreddit=subreddit, post_id=line.strip())
            )
        db.session.commit()

    def to_dict(self):
        json_dict = {}
        json_dict["username"] = self.username
        json_dict["subreddit"] = self.subreddit
        json_dict["post_id"] = self.post_id

        return json_dict

    @classmethod
    def jsonify_query(self, query):
        result = {"posts": []}
        for post in query:
            result["posts"].append(post.to_dict())

        return jsonify(result)

    @classmethod
    def get_subreddit_posts(cls, username: str, subreddit: str):
        return cls.jsonify_query(
            cls.query.filter_by(username=username, subreddit=subreddit)
        )

    @classmethod
    def add_post(cls, username: str, subreddit: str, post_id: str):
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
    ):
        result = []
        for thing in posts:
            result.append(cls.add_post(username, thing["subreddit"], thing["post_id"]))

        return result

    # should be used as a helper function
    @classmethod
    def check_post(cls, username: str, subreddit: str, post_id: str):
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
    def check_posts(cls, username: str, posts: list[dict[str, str]]):
        result = []
        for post in posts:
            post_dict = cls.check_post(username, post["subreddit"], post["post_id"])

            result.append(post_dict)

        return result


@posts_page.get("/")
@token_required
def check_multiple_posts(current_user: User):
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
    posts = Post.query.filter_by(username=current_user.username, subreddit=subreddit)
    return Post.jsonify_query(posts), 200


@posts_page.post("/")
@token_required
def add_subreddit_posts(current_user: User):
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
