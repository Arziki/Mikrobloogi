from flask import render_template, flash, redirect, url_for
from app import app
from app.forms import LoginForm
from flask_login import current_user, login_user
from app.models import User
from flask_login import logout_user
from flask_login import login_required   # limiting access to unregistered or unlogged in users
from flask import request   # attempt to access page, while not logged in
from werkzeug.urls import url_parse

from app import db      #User Registation View related
from app.forms import RegistrationForm     # Registration view related
from app.forms import  PostForm    # Blog post form Pagination
from app.models import Post    # Pagination related
from datetime import datetime   # to record time of last visit

from app.forms import EditProfileForm  # Linking edit profile related additions



        
    
			
			# flash('Login requester for user {}, remember_me={}'.format(
			# logform.username.data, logform.remember_me.data))
	# 	return redirect(url_for('index'))
	# return render_template('login.html', title='Sign In', form=logform)


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
	form = PostForm()
	if form.validate_on_submit():
		post = Post(body=form.post.data, author=current_user)
		db.session.add(post)
		db.session.commit()
		flash('Your post is now live!')
		return redirect(url_for('index'))
	page = request.args.get('page', 1, type=int)
	posts = current_user.followed_posts().paginate(
		page, app.config['POSTS_PER_PAGE'], False)
	next_url = url_for('index', page=posts.next_num) \
		if posts.has_next else None
	prev_url = url_for('index', page=posts.prev_num) \
		if posts.has_prev else None
	# posts = [
	# {
	# 		'author': {'username' : 'John'},
	# 		'body' : 'Seitseman Veljesta'
	# },
	# {
	# 		'author': {'username' : 'Susan'},
	# 		'body' : 'An Ear to the Ground'
	# },
	# {
	# 		'author': {'username' : 'Mummu'},
	# 		'body' : 'Beleive This, Beleive Anything'
	# },
	# {
	# 		'author': {'username' : 'Wiljami'},
	# 		'body' : 'Eyes Wide Shot'
	# },
	# {
	# 		'author': {'username' : ' Aaroni'},
	# 		'body' : 'I will Bury My Dead'
	# },
	# {
	# 		'author': {'username' : 'Juju'},
	# 		'body' : 'Koffin from Hongkon'
	# },
	# {
	# 		'author' : {'username' : 'Santtu'},
	# 		'body' : 'Grand Theft Auto !' 
	# }

	# ]
	
	return render_template('index.html', title='Home Page', form=form, posts=posts.items, next_url=next_url, prev_url=prev_url)

@app.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('index', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('index', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template("index.html", title='Explore', posts=posts.items, next_url=next_url, prev_url=prev_url)


@app.route('/login', methods=['GET', 'POST'])
def login():
	if current_user.is_authenticated:
		return redirect(url_for('index'))
	logform = LoginForm()
	if logform.validate_on_submit():
		user = User.query.filter_by(username=logform.username.data).first()
		if user is None or not user.check_password(logform.password.data):
			flash ('Invalid username or password')
			return redirect(url_for('login'))
		login_user(user, remember=logform.remember_me.data)
		next_page = request.args.get('next')
		if not next_page or url_parse (next_page).netloc != '':
			next_page = url_for ('index')
		return redirect (next_page)
		return redirect(url_for('index'))
	return render_template('login.html', title='Sign In', form=logform)

@app.route('/logout')
def logout():
	logout_user()
	return redirect(url_for('index'))


@app.route('/register', methods=['GET','POST'])
def register():
	if current_user.is_authenticated:
		return redirect(url_for('index'))
	Regform = RegistrationForm()
	if Regform.validate_on_submit():
		user = User(username=Regform.username.data, email=Regform.email.data)
		user.set_password(Regform.password.data)
		db.session.add(user)
		db.session.commit()
		flash('Onneksi Olkoon, olet rekisteroinut uutena käyttäjänä!')
		return redirect(url_for('login'))
	return render_template('register.html', title='Register', form=Regform)


@app.route('/user/<username>')
@login_required
def user(username):
	user = User.query.filter_by(username=username).first_or_404()
	page = request.args.get('page', 1, type=int)
	posts = Post.query.order_by(Post.timestamp.desc()).paginate(
		page, app.config['POSTS_PER_PAGE'], False)
	next_url = url_for('index', page=posts.next_num) \
		if posts.has_next else None
	prev_url = url_for('index', page=posts.prev_num) \
		if posts.has_prev else None
	return render_template('user.html', user=user, posts=posts.items, next_url=next_url, prev_url=prev_url)
	# posts = [
	# {'author': user, 'body': 'Test post #1'},
	# {'author': user, 'body': 'Test post #2'}
	# ]

	
@app.before_request
def before_request():
	if current_user.is_authenticated:
		current_user.last_seen = datetime.utcnow()
		db.session.commit()



@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
	EditProform = EditProfileForm(current_user.username)
	if EditProform.validate_on_submit():
		current_user.username = EditProform.username.data
		current_user.about_me = EditProform.about_me.data
		db.session.commit()
		flash('Your changes have been saved.')
		return redirect(url_for('edit_profile'))
	elif request.method == 'GET':
		EditProform.username.data = current_user.username
		EditProform.about_me.data = current_user.about_me
	return render_template('edit_profile.html', title='Edit Profile', form=EditProform)
	

@app.route('/follow/<username>')
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} not found.'.format(username))
        return redirect(url_for('index'))
    if user == current_user:
        flash('You cannot follow yourself!')
        return redirect(url_for('user', username=username))
    current_user.follow(user)
    db.session.commit()
    flash('You are following {}!'.format(username))
    return redirect(url_for('user', username=username))


@app.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} not found.'.format(username))
        return redirect(url_for('index'))
    if user == current_user:
        flash('You cannot unfollow yourself!')
        return redirect(url_for('user', username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash('You are not following {}.'.format(username))
    return redirect(url_for('user', username=username))


