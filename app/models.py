from datetime import datetime
from app import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from hashlib import md5

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    pw_hash = db.Column(db.String(128))
    posts = db.relationship('Post', backref='author', lazy='dynamic')

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

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Post body: "%s" user_id:"%s">' % (self.body, self.user_id)

# Flask-Login (LoginManager module) retrieves the id and load into memory
@login.user_loader
def load_user(id):
    # Flask-Login passes a string, needs to convert to int
    return User.query.get(int(id))
