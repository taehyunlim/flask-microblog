from datetime import datetime
from time import time
from app import db, login
from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from hashlib import md5
from app.search import add_to_index, remove_from_index, query_index
import jwt

# Create an association table for followers
followers = db.Table('followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    pw_hash = db.Column(db.String(128))
    about_me = db.Column(db.String(140))
    datetime_joined = db.Column(db.DateTime, default=datetime.utcnow)
    datetime_last_seen = db.Column(db.DateTime, default=datetime.utcnow)

    # Posts: One-to-Many relationship
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    # Followers: Many-to-Many relationship
    followed = db.relationship(
        'User', # Self-referential
        secondary=followers, # Association table defined above
        primaryjoin=(followers.c.follower_id == id), # How left-side entity is linked: User's `id` matches the `follower_id` field of the association table
        secondaryjoin=(followers.c.followed_id == id), # How the right-side entity (followed user) is linked.
        backref=db.backref('followers', lazy='dynamic'), # How this relationship will be accessed from the right-side entity (followed)
        lazy='dynamic' # `dynamic` sets up the query to not run until specifically requested
    )

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_pw(self, pw):
        self.pw_hash = generate_password_hash(pw)

    def check_pw(self, pw):
        return check_password_hash(self.pw_hash, pw)

    def avatar(self, size):
        # Encode email string as bytes and then store the hexadecimal digest string
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(digest, size)

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        return self.followed.filter(
            followers.c.followed_id == user.id).count() > 0

    def followed_posts(self):
        followed = Post.query.join(
            followers, (followers.c.followed_id == Post.user_id)).filter(
                followers.c.follower_id == self.id)
        own = Post.query.filter_by(user_id=self.id)
        return followed.union(own).order_by(Post.timestamp.desc())

    def get_reset_pw_token(self, expires_in=600):
        return jwt.encode(
            {'reset_pw': self.id, 'exp': time() + expires_in}, current_app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

    @staticmethod
    def verify_reset_pw_token(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])['reset_pw']
        except:
            return
        return User.query.get(id)

class SearchableMixin(object):
    # Methods receive a class and not an instance as its first arg
    # More on classmethods: https://goo.gl/vGDMsv
    @classmethod
    def search(cls, expression, page, per_page):
        ids, total = query_index(cls.__tablename__, expression, page, per_page)
        if total == 0:
            # No results found, return 0
            return cls.query.filter_by(id=0), 0
        when = []
        # Fabricating `when` statement for the query
        for i in range(len(ids)):
            when.append((ids[i], i))
        # when = [({ '_index': '', '_id': '', '_score': ''}, 1), ({ } ,2), ...]
        # order_by/case syntax: https://goo.gl/t8mwSR
        return cls.query.filter(cls.id.in_(ids)).order_by(
            db.case(when, value=cls.id)), total

    @classmethod
    def before_commit(cls, session):
        # Create a session._changes dictionary to save the objects throughout the session, until ES index is updated
        session._changes = {
            'add': list(session.new),
            'update': list(session.dirty),
            'delete': list(session.deleted)
        }

    @classmethod
    def after_commit(cls, session):
        for obj in session._changes['add']:
            # Q: Why use isinstance?
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes['update']:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes['delete']:
            if isinstance(obj, SearchableMixin):
                remove_from_index(obj.__tablename__, obj)
        # Clear session changes
        session._changes = None

    @classmethod
    def reindex(cls):
        for obj in cls.query:
            add_to_index(cls.__tablename__, obj)

db.event.listen(db.session, 'before_commit', SearchableMixin.before_commit)
db.event.listen(db.session, 'after_commit', SearchableMixin.after_commit)

class Post(SearchableMixin, db.Model):
    __searchable__ = ['body']
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    language = db.Column(db.String(5))

    def __repr__(self):
        return '<Post body: "%s" user_id:"%s">' % (self.body, self.user_id)

# Flask-Login (LoginManager module) retrieves the id and load into memory
@login.user_loader
def load_user(id):
    # Flask-Login passes a string, needs to convert to int
    return User.query.get(int(id))
