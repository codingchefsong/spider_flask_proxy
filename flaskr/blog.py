from flask import (
    Flask, Blueprint, flash, g, redirect, render_template, request, url_for
)
# from flask import Flask, flash, request, redirect, url_for
from werkzeug.exceptions import abort

from werkzeug.utils import secure_filename

import os

from flaskr.auth import login_required
from flaskr.db import get_db

bp = Blueprint('blog', __name__)

# upload config
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(APP_ROOT, 'uploads')
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.errorhandler(413)
def too_large(e):
    return "File is too large", 413


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
    return render_template('blog/home.html', records=records)


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

        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            return redirect(url_for('blog.index'))

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO post (title, body, author_id)'
                ' VALUES (?, ?, ?)',
                (title, body, g.user['id'])
            )
            db.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/create.html')


def get_post(id, check_author=True):
    post = get_db().execute(
        'SELECT p.id, author_id, created, ip, port, delay'
        ' FROM proxy p JOIN user u ON p.author_id = u.id'
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

    if request.method == 'POST':
        ip = request.form['ip']
        port = request.form['port']
        delay = request.form['delay']
        error = None

        if not ip:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE proxy SET ip = ?, port = ?, delay = ?'
                ' WHERE id = ?',
                (ip, port, delay, id)
            )
            db.commit()
            return redirect(url_for('blog.dashboard'))

    return render_template('blog/update.html', post=post)


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_post(id)
    db = get_db()
    db.execute('DELETE FROM proxy WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('blog.dashboard'))
