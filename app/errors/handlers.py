from flask import render_template
from app import db
from app.errors import bp

@bp.app_errorhandler(404)
def not_found_error(error):
    # Return the error code as a second return value
    return render_template('errors/404.html'), 404

@bp.app_errorhandler(500)
def internal_error(error):
    # Issue a session rollback in case any failed db sessions do not interfere with db acceesses
    db.session.rollback()
    return render_template('errors/500.html'), 500
