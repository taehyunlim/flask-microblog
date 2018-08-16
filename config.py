import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    # Get secret_key from environment variable or use hardcoded key
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'test_secret_key'
    # Flask-SQLAlchemy config
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
