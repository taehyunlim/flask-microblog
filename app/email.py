from flask import render_template, current_app
from flask_mail import Message
from app import mail
from threading import Thread # Async process module

def send_async_email(appl, msg):
    with appl.app_context():
        mail.send(msg)

def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    # mail.send(msg)
    # Instead of .send method, invoke a background thread to send email
    Thread(target=send_async_email, args=(current_app._get_current_object(), msg)).start()
