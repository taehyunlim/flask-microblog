from app import application, db
from flask import render_template

@application.errorhandler(404)
def not_found_error(error):
    # Return the error code as a second return value
    return render_template('404.html'), 404

@application.errorhandler(500)
def internal_error(error):
    # Issue a session rollback in case any failed db sessions do not interfere with db acceesses
    db.session.rollback()
    return render_template('500.html'), 500
