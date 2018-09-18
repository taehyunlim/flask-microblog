from app import db
from flask import render_template, flash, redirect, request, url_for, g, jsonify, current_app
from werkzeug.urls import url_parse
from app.main.forms import EditProfileForm, PostForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Post
from datetime import datetime
from flask_babel import _, get_locale
from guess_language import guess_language
from app.translate import translate
from app.main import bp
from app.main.forms import SearchForm

@bp.before_request
def before_request():
    if current_user.is_authenticated:
        # Upon referencing `current_user` Flask-Login will invoke the user loader callback function, which will run a database query that will put the target user in the database session
        current_user.datetime_last_seen = datetime.utcnow()
        db.session.commit()
        # Instantiate the search form in the `before_request` handler
        g.search_form = SearchForm()
    # Store selected language in `flask.g` (global object) to access from the base template
    # `flask.g` variable is specific to each request and each client
    g.locale = str(get_locale())


@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
# @login_required passes `next` query string arg (/login?next=/{'an endpoint'})
@login_required
def index():
    # Pagination: Page # from query string arg
    page = request.args.get('page', 1, type=int)
    form = PostForm()
    if form.validate_on_submit():
        # Add language detection
        guess_lang = guess_language(form.post.data)
        if guess_lang == 'UNKNOWN' or len(guess_lang) > 5:
            guess_lang = ''
        # Write the post to db
        post = Post(body=form.post.data, author=current_user, language=guess_lang)
        db.session.add(post)
        db.session.commit()
        flash('Posted successfully.')
        return redirect(url_for('main.index'))
    # Pagination: '# of posts per page' setting is in config
    posts = current_user.followed_posts().paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    # Pagination: next and prev page #s
    next_url = url_for('main.index', page=posts.next_num) if posts.has_next else None
    prev_url = url_for('main.index', page=posts.prev_num) if posts.has_prev else None
    return render_template('index.html', title='Home', form=form, posts=posts.items, next_url=next_url, prev_url=prev_url)

@bp.route('/GET', methods=['GET'])
def test():
    return "Test"

@bp.route('/user/<username>')
@login_required
def user(username):
    # Sends 404 error back to client if no results found
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    posts = user.posts.order_by(Post.timestamp.desc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.user', username=user.username, page=posts.next_num) if posts.has_next else None
    prev_url = url_for('main.user', username=user.username, page=posts.prev_num) if posts.has_prev else None
    return render_template('user.html', user=user, posts=posts.items, next_url=next_url, prev_url=prev_url)

@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('main.user', username=current_user.username))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile', form=form)

@bp.route('/follow/<username>')
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} not found.'.format(username))
        return redirect(url_for('main.index'))
    if user == current_user:
        flash('One does not simply follow himself!')
        return redirect(url_for('main.user', username=username))
    current_user.follow(user)
    db.session.commit()
    flash('You are now following {}.'.format(username))
    return redirect(url_for('main.user', username=username))

@bp.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(_('User %(username)s not found.', username=username))
        return redirect(url_for('main.index'))
    if user == current_user:
        flash('You cannot unfollow yourself.')
        return redirect(url_for('main.user', username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash(_('You\'re not following %(username)s', username=username))
    return redirect(url_for('main.user', username=username))

@bp.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.explore', page=posts.next_num) if posts.has_next else None
    prev_url = url_for('main.explore', page=posts.prev_num) if posts.has_prev else None
    return render_template('index.html', title='Explore', posts=posts.items, next_url=next_url, prev_url=prev_url)

@bp.route('/translate', methods=['POST'])
@login_required
def translate_text():
    return jsonify({'text': translate(request.form['text'], request.form['source_lang'], request.form['dest_lang'])})

@bp.route('/search')
@login_required
def search():
    if not g.search_form.validate():
        return redirect(url_for('main.explore'))
    query = g.search_form.q.data
    page = request.args.get('page', 1, type=int)
    posts, total = Post.search(g.search_form.q.data, page, current_app.config['POSTS_PER_PAGE'])
    next_url = url_for('main.search', q=g.search_form.q.data, page = page+1) if total > page * current_app.config['POSTS_PER_PAGE'] else None
    prev_url = url_for('main.search', q=g.search_form.q.data, page = page-1) if page > 1 else None
    return render_template('search.html', title=_('Search'), posts=posts, next_url=next_url, prev_url=prev_url, query=query)

@bp.route('/user/<username>/modal')
@login_required
def user_modal(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template('user_modal.html', user=user)
