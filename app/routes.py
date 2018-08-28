from app import application, db
from flask import render_template, flash, redirect, request, url_for
from werkzeug.urls import url_parse
from app.forms import LoginForm, RegistrationForm, EditProfileForm, PostForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Post
from datetime import datetime

@application.before_request
def before_request():
    if current_user.is_authenticated:
        # Upon referencing `current_user` Flask-Login will invoke the user loader callback function, which will run a database query that will put the target user in the database session
        current_user.datetime_last_seen = datetime.utcnow()
        db.session.commit()

@application.route('/', methods=['GET', 'POST'])
@application.route('/index', methods=['GET', 'POST'])
# @login_required passes `next` query string arg (/login?next=/{'an endpoint'})
@login_required
def index():
    # Pagination: Page # from query string arg
    page = request.args.get('page', 1, type=int)
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.post.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Posted successfully.')
        return redirect(url_for('index'))
    # Pagination: '# of posts per page' setting is in config
    posts = current_user.followed_posts().paginate(
        page, application.config['POSTS_PER_PAGE'], False)
    # Pagination: next and prev page #s
    next_url = url_for('index', page=posts.next_num) if posts.has_next else None
    prev_url = url_for('index', page=posts.prev_num) if posts.has_prev else None
    return render_template('index.html', title='Home', form=form, posts=posts.items, next_url=next_url, prev_url=prev_url)

@application.route('/GET', methods=['GET'])
def test():
    return "Test"

@application.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        # note: current_user represents the client of the request (Flask-Login from_object)
        return redirect(url_for('index'))
    # From `app.forms`
    form = LoginForm()
    if form.validate_on_submit():
        # For debugging
        # flash('Login requested for user {}, remember_me={}'.format(form.username.data, form.remember_me.data))
        # Log a user in
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_pw(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        # Register the user as logged in (persist throughout session)
        login_user(user, remember=form.remember_me.data)
        # request.args attribute exposes the contents of the query string from @login_required decorator
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

@application.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_pw(form.pw2.data)
        db.session.add(user)
        db.session.commit()
        flash('Registration complete.')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@application.route('/user/<username>')
@login_required
def user(username):
    # Sends 404 error back to client if no results found
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    posts = user.posts.order_by(Post.timestamp.desc()).paginate(
        page, application.config['POSTS_PER_PAGE'], False)
    next_url = url_for('user', username=user.username, page=posts.next_num) if posts.has_next else None
    prev_url = url_for('user', username=user.username, page=posts.prev_num) if posts.has_prev else None
    return render_template('user.html', user=user, posts=posts.items, next_url=next_url, prev_url=prev_url)

@application.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile', form=form)

@application.route('/follow/<username>')
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} not found.'.format(username))
        return redirect(url_for('index'))
    if user == current_user:
        flash('One does not simply follow himself!')
        return redirect(url_for('user', username=username))
    current_user.follow(user)
    db.session.commit()
    flash('You are now following {}.'.format(username))
    return redirect(url_for('user', username=username))

@application.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} not found'.format(username))
        return redirect(url_for('index'))
    if user == current_user:
        flash('You cannot unfollow yourself.')
        return redirect(url_for('user', username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash('You are not following {}.'.format(username))
    return redirect(url_for('user', username=username))

@application.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(
        page, application.config['POSTS_PER_PAGE'], False)
    next_url = url_for('explore', page=posts.next_num) if posts.has_next else None
    prev_url = url_for('explore', page=posts.prev_num) if posts.has_prev else None
    return render_template('index.html', title='Explore', posts=posts.items, next_url=next_url, prev_url=prev_url)
