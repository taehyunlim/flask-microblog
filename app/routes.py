from app import application
from flask import render_template, flash, redirect, request
from werkzeug.urls import url_parse
from app.forms import LoginForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User

@application.route('/')
@application.route('/index')
# @login_required passes `next` query string arg (/login?next=/{'an endpoint'})
@login_required
def index():
    return render_template('index.html', title='Home', posts=posts);

@application.route('/GET', methods=['GET'])
def test():
    return "Test"

@application.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        # note: current_user represents the client of the request (Flask-Login from_object)
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        # For debugging
        flash('Login requested for user {}, remember_me={}'.format(
            form.username.data, form.remember_me.data))
        # Log a user in
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_pw(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        # Register the user as logged in (persist throughout session)
        login_user(user, remember=form.remember_me.data)
        # requests.args attribute exposes the contents of the query string from @login_required decorator
        next_page = request.args.get('next')
        # if URL includes a `next` arg that is set to a full URL, redirect to the index page
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
        return redirect(url_for('index'))
    return render_template('login.html', title='Sign In', form=form)

@application.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))
