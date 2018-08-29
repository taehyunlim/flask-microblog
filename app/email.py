from flask import render_template
from flask_mail import Message
from app import mail, application
from threading import Thread # Async process module

def send_asyn_email(appl, msg):
    with appl.app_context():
        mail.send(msg)

def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    # mail.send(msg)
    # Instead of .send method, invoke a background thread to send email
    Thread(target=send_asyn_email, args=(application, msg)).start()

def send_pw_reset_email(user):
    token = user.get_reset_pw_token()
    send_email('[Microblog] Reset your password',
        sender=application.config['ADMINS'][0],
        recipients=[user.email],
        text_body=render_template('email/reset_pw.txt', user=user, token=token),
        html_body=render_template('email/reset_pw.html', user=user, token=token)
    )
