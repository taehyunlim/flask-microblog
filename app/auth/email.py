from flask import render_template, current_app
from app.email import send_email
from flask_babel import _

def send_pw_reset_email(user):
    token = user.get_reset_pw_token()
    send_email('[Microblog] Reset your password',
        sender=current_app.config['ADMINS'][0],
        recipients=[user.email],
        text_body=render_template('email/reset_pw.txt', user=user, token=token),
        html_body=render_template('email/reset_pw.html', user=user, token=token)
    )
