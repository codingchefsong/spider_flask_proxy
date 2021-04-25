import uuid
import ast

from flask import (
    Flask, Blueprint, flash, g, redirect, render_template, request, url_for, current_app
)
# from flask import Flask, flash, request, redirect, url_for
from werkzeug.exceptions import abort

from werkzeug.utils import secure_filename

import os

from wtforms.validators import DataRequired

from flaskr.auth import login_required
from flaskr.db import get_db

bp = Blueprint('blog', __name__)

# upload config
# APP_ROOT = os.path.dirname(os.path.abspath(__file__))
# UPLOAD_FOLDER = os.path.join(APP_ROOT, 'uploads')
# ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
# app = Flask(__name__)
# app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# upload v2
from flask_uploads import UploadSet, configure_uploads, IMAGES, patch_request_class
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import SubmitField, StringField


# app = Flask(__name__)
# app.config['SECRET_KEY'] = 'I have a dream'
# basedir = os.path.abspath(os.path.dirname(__file__))
# app.config['UPLOADED_PHOTOS_DEST'] = os.path.join(basedir, 'uploads')  # you'll need to create a folder named uploads

# photos = UploadSet('photos', IMAGES)
# configure_uploads(app, photos)
# patch_request_class(app)


class UploadForm(FlaskForm):
    name = StringField('name', validators=[DataRequired()])
    photos = UploadSet('photos', IMAGES)
    photo = FileField(validators=[
        FileAllowed(photos, u'只能上传图片！'),
        FileRequired(u'文件未选择！')])
    submit = SubmitField(u'上传')


photos = UploadSet('photos', IMAGES)
app = current_app


@bp.route('/upload', methods=('GET', 'POST'))
@login_required
def upload():
    form = UploadForm()
    if form.validate_on_submit():
        name = request.form['name']
        fileurls = []
        for f in request.files.getlist('photo'):
            filename = uuid.uuid4().hex
            fileurls.append(photos.url(filename))
            photos.save(f, name=filename + '.')
        success = True
        db = get_db()
        db.execute(
            'INSERT INTO upload (title, body, author_id, file_url)'
            ' VALUES (?, ?, ?, ?)',
            (name, 'body', g.user['id'], str(fileurls))
        )
        db.commit()
    else:
        success = False
    return render_template('blog/upload.html', form=form, success=success)
    # return render_template('blog/upload.html', form=form, file_url=file_url)


@bp.route('/manage')
def manage_file():
    files_list = os.listdir(app.config['UPLOADED_PHOTOS_DEST'])
    return render_template('blog/manage.html', files_list=files_list)


@bp.route('/open/<filename>')
def open_file(filename):
    file_url = photos.url(filename)
    return render_template('blog/browser.html', file_url=file_url)


@bp.route('/delete/<filename>')
def delete_file(filename):
    file_path = photos.path(filename)
    os.remove(file_path)
    return redirect(url_for('blog/manage_file'))


@bp.route('/home')
def home():
    db = get_db()
    posts = db.execute(
        'SELECT p.id, title, body, created, author_id, username'
        ' FROM upload p JOIN user u ON p.author_id = u.id'
        ' ORDER BY created DESC'
    ).fetchall()
    return render_template('blog/home.html', posts=posts)


@bp.route('/proxy')
def proxy():
    # print(id)
    db = get_db()
    # records = db.execute(
    #     'SELECT p.id, author_id, created, ip, port, delay, username'
    #     ' FROM socks p JOIN user u ON p.author_id = u.id'
    #     ' WHERE delay IS NOT NULL'
    #     ' ORDER BY created DESC, delay ASC'
    # ).fetchall()
    records = db.execute(
        'SELECT ip, port'
        ' FROM proxy p JOIN user u ON p.author_id = u.id'
        ' WHERE updated =(SELECT MAX(updated) FROM proxy)'
        ' ORDER BY delay ASC'
    ).fetchall()
    # record = records[id]
    return render_template('proxy.html', records=records)


@bp.route('/pac<int:id>')
def pac(id):
    # print(id)
    db = get_db()
    records = db.execute(
        'SELECT ip, port, delay, updated, author_id, username'
        ' FROM proxy p JOIN user u ON p.author_id = u.id'
        ' WHERE updated =(SELECT MAX(updated) FROM proxy)'
        ' ORDER BY delay ASC'
    ).fetchall()
    record = records[id]
    return render_template('pac.html', records=record)


@bp.route('/next')
def pac_next():
    db = get_db()
    records = db.execute(
        'SELECT ip, port, delay, updated, author_id, username'
        ' FROM proxy p JOIN user u ON p.author_id = u.id'
        ' WHERE updated =(SELECT MAX(updated) FROM proxy)'
        ' ORDER BY delay ASC'
    ).fetchall()
    if len(records) >= 2:
        ip = records[0]['ip']
        print("Delete proxy record.")
        # db.execute('DELETE FROM proxy WHERE ip = ?', (ip,))
        db.execute("UPDATE proxy SET delay = ? WHERE ip = ?", (99999, ip))
    db.commit()
    return redirect(url_for('blog.dashboard'))


@bp.route('/dashboard')
@login_required
def dashboard():
    db = get_db()

    records = db.execute(
        'SELECT p.id, author_id, created, updated, ip, port, username'
        ' FROM proxy p JOIN user u ON p.author_id = u.id'
        ' ORDER BY created DESC'
    ).fetchall()

    return render_template('blog/dashboard.html', records=records)


@bp.route('/')
@login_required
def index():
    db = get_db()
    # develop 环境可以工作，linux 不能执行 NULLS LAST
    # records = db.execute(
    #     'SELECT p.id, author_id, created, ip, port, delay, username'
    #     ' FROM proxy p JOIN user u ON p.author_id = u.id'
    #     ' ORDER BY created DESC, delay ASC NULLS LAST'
    # ).fetchall()

    records = db.execute(
        'SELECT p.id, ip, port, delay, created, updated, author_id, username'
        ' FROM proxy p JOIN user u ON p.author_id = u.id'
        ' WHERE updated =(SELECT MAX(updated) FROM proxy)'
        ' ORDER BY delay ASC'
    ).fetchall()
    return render_template('blog/index.html', records=records)


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    # print(UPLOAD_FOLDER)
    # print(os.path.dirname(os.path.abspath(__file__)))
    # print(os.path.join(app.config['UPLOAD_FOLDER']))
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO upload (title, body, author_id)'
                ' VALUES (?, ?, ?)',
                (title, body, g.user['id'])
            )
            db.commit()
            return redirect(url_for('blog.index'))
    return render_template('blog/create.html')


def get_post(id, check_author=True):
    post = get_db().execute(
        'SELECT p.id, title, body, created, author_id, username, file_url'
        ' FROM upload p JOIN user u ON p.author_id = u.id'
        ' WHERE p.id = ?',
        (id,)
    ).fetchone()

    if post is None:
        abort(404, "Post id {0} doesn't exist.".format(id))

    if check_author and post['author_id'] != g.user['id']:
        abort(403)

    return post


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    post = get_post(id)
    print(post['file_url'])
    fileurls = ast.literal_eval(post['file_url'])

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE post SET title = ?, body = ?'
                ' WHERE id = ?',
                (title, body, id)
            )
            db.commit()
            return redirect(url_for('blog.index'))
    print(fileurls)
    return render_template('blog/update.html', post=post, fileurls=fileurls)


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_post(id)
    db = get_db()
    db.execute('DELETE FROM proxy WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('blog.dashboard'))
