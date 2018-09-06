import logging, os
from flask import Flask, request
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from logging.handlers import SMTPHandler, RotatingFileHandler
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_babel import Babel

application = Flask(__name__)
application.config.from_object(Config)
db = SQLAlchemy(application)
migrate = Migrate(application, db)
login = LoginManager(application)
login.login_view = 'login'
mail = Mail(application)
bootstrap = Bootstrap(application)
moment = Moment(application)
babel = Babel(application)

from app import routes, models, errors

# Add SMTPHandler instace to the logger object to log errors by email
if not application.debug:
    # Only enable email logger if the email server configs info exists
    # TEST: (venv) python -m smtpd -n -c DebuggingServer localhost:8025
    if application.config['MAIL_SERVER']:
        auth = None
        if application.config['MAIL_USERNAME'] or application.config['MAIL_PASSWORD']:
            auth = (application.config['MAIL_USERNAME'], application.config['MAIL_PASSWORD'])
        secure = None
        if application.config['MAIL_USE_TLS']:
            secure = ()
        mail_handler = SMTPHandler(
            mailhost=(application.config['MAIL_SERVER'], application.config['MAIL_PORT']),
            fromaddr='no-reply@' + application.config['MAIL_SERVER'],
            toaddrs=application.config['ADMINS'], subject='Microblog Failure',
            credentials=auth, secure=secure)
        mail_handler.setLevel(logging.ERROR)
        application.logger.addHandler(mail_handler)

    # Logging to a file
    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_handler = RotatingFileHandler('logs/Microblog', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s: %(lineno)d]'))
    file_handler.setLevel(logging.INFO)
    application.logger.addHandler(file_handler)
    # Logging categories: DEBUG, INFO, WARNING, ERROR and CRITICAL
    application.logger.setLevel(logging.INFO)
    application.logger.info('Microblog startup')

@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(application.config['LANGUAGES'])
    # return 'ko'
