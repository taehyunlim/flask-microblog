from datetime import datetime
from time import time
from app import db, login
from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from hashlib import md5
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

class Post(db.Model):
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
