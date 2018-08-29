import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    # Get secret_key from environment variable or use hardcoded key
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'test_secret_key'
    # Flask-SQLAlchemy config
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Pagination global config
    POSTS_PER_PAGE = 10
    # Email config
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = ['taehyun.lim@gmail.com']
