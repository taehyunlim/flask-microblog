from flask import render_template
from flask_mail import Message
from app import mail, application

def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    mail.send(msg)

def send_pw_reset_email(user):
    token = user.get_reset_pw_token()
    send_email('[Microblog] Reset your password',
        sender=application.config['ADMINS'][0],
        recipients=[user.email],
        text_body=render_template('email/reset_pw.txt', user=user, token=token),
        html_body=render_template('email/reset_pw.html', user=user, token=token)
    )
