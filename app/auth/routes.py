from app import application, db
from app.auth import bp
from app.auth.forms import LoginForm, RegistrationForm, ResetPasswordRequestForm, ResetPasswordForm
from app.auth.email import send_pw_reset_email
from flask import render_template, flash, redirect, request, url_for, g, jsonify
from werkzeug.urls import url_parse
from flask_login import current_user, login_user, logout_user
from app.models import User
from flask_babel import _

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        # note: current_user represents the client of the request (Flask-Login from_object)
        return redirect(url_for('main.index'))
    # From `app.forms`
    form = LoginForm()
    if form.validate_on_submit():
        # For debugging
        # flash('Login requested for user {}, remember_me={}'.format(form.username.data, form.remember_me.data))
        # Log a user in
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_pw(form.password.data):
            flash(_('Invalid username or password'))
            return redirect(url_for('auth.login'))
        # Register the user as logged in (persist throughout session)
        login_user(user, remember=form.remember_me.data)
        # request.args attribute exposes the contents of the query string from @login_required decorator
        next_page = request.args.get('next')
        # if URL includes a `next` arg that is set to a full URL, redirect to the index page
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('main.index')
        return redirect(next_page)
    return render_template('auth/login.html', title='Sign In', form=form)

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_pw(form.pw2.data)
        db.session.add(user)
        db.session.commit()
        flash('Registration complete.')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', title='Register', form=form)

@bp.route('/reset_pw_request', methods=['GET', 'POST'])
def reset_pw_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_pw_reset_email(user)
        flash('Check your email for the instructions to reset your password')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_pw_request.html', title='Reset Password', form=form)

@bp.route('/reset_pw/<token>', methods=['GET', 'POST'])
def reset_pw(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    user = User.verify_reset_pw_token(token)
    if not user:
        return redirect(url_for('main.index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_pw(form.pw.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_pw.html', form=form)
