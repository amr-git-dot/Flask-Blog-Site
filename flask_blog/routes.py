from flask import render_template, url_for, flash, redirect, request, abort
from flask_blog.forms import RegistrationForm, LoginForm, UpdateAccountForm, NewPostForm
from flask_blog.models import User, Post
from flask_blog import app, db,bcrypt
from flask_login import login_user, current_user, logout_user, login_required
import os
import secrets
from PIL import Image

 


@app.route("/")
@app.route("/home")
def home():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=5)
    return render_template('home.html', posts=posts)


@app.route("/about")
def about():
    return render_template('about.html', title='About')


@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_pw = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data,email = form.email.data,password=hashed_pw)
        db.session.add(user)
        db.session.commit()
        flash('your account has been created successfuly now you can log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email= form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            flash('Login Successful. ', 'success')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))


def savepicture(form_picture):
    random_hex = secrets.token_hex(8)
    _,f_ext = os.path.splitext(form_picture.filename)
    f_name = random_hex + f_ext 
    picture_path = os.path.join(app.root_path,'static/profile_pic',f_name)
    output_size = (125,125)
    i =  Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)
    return f_name
    

@app.route("/account",methods=["POST","GET"])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            profile_pic = savepicture(form.picture.data)
            current_user.image_file = profile_pic
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Account updated successfuly','success')
        return redirect(url_for('account'))
    elif request.method == "GET":
        form.username.data = current_user.username
        form.email.data = current_user.email 
    image_file = url_for('static', filename='profile_pic/'+current_user.image_file)
    return render_template('account.html',title='Account', image_file=image_file, form=form)


@app.route("/newpost", methods=["GET","POST"])
@login_required
def newpost():
    form =NewPostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data,content=form.content.data,author=current_user)
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('newpost.html', title='New Post',form=form)

@app.route("/post/<int:post_id>")
def post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post.html', title=post.title,post=post)

@app.route("/post/<int:post_id>/update", methods=["GET","POST"])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = NewPostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash('Your post updated successfuly','success')
        return redirect(url_for('post', post_id=post.id))
    if request.method == "GET":
        form.title.data = post.title
        form.content.data = post.content
    return render_template('newpost.html', title='Update post', legend='Update Post',form=form)

@app.route("/post/<int:post_id>/delete", methods=["POST"])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = NewPostForm()
     
    db.session.delete(post)
    db.session.commit()
    flash('Your post deleted successfuly','success')
    return redirect(url_for('home'))


@app.route("/user/<string:username>")
def user_posts(username):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(author=user)\
        .order_by(Post.date_posted.desc())\
        .paginate(page=page, per_page=5)
    return render_template('user_posts.html', posts=posts, user=user)