from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)

bp = Blueprint('blog', __name__)


@bp.route('/pac<int:id>')
def pac(id):
    # print(id)
    db = get_db()
    records = db.execute(
        'SELECT p.id, author_id, created, ip, port, delay, username'
        ' FROM proxy p JOIN user u ON p.author_id = u.id'
        ' WHERE delay IS NOT NULL'
        ' ORDER BY created DESC, delay ASC'
    ).fetchall()
    record = records[id]
    return render_template('pac.html', records=record)


@bp.route('/next')
def pac_next():
    db = get_db()
    records = db.execute(
        'SELECT p.id, author_id, created, ip, port, delay, username'
        ' FROM proxy p JOIN user u ON p.author_id = u.id'
        ' WHERE delay IS NOT NULL'
        ' ORDER BY created DESC, delay ASC'
    ).fetchall()
    if len(records) >= 2:
        ip = records[0]['ip']
        print("Delete proxy record.")
        db.execute('DELETE FROM proxy WHERE ip = ?', (ip,))
    db.commit()
    return redirect(url_for('blog.dashboard'))


@bp.route('/dashboard')
@login_required
def dashboard():
    db = get_db()

    records = db.execute(
        'SELECT p.id, author_id, created, ip, port, delay, username'
        ' FROM proxy p JOIN user u ON p.author_id = u.id'
        ' ORDER BY created DESC, delay DESC'
    ).fetchall()

    return render_template('blog/home.html', records=records)


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
        'SELECT p.id, author_id, created, ip, port, delay, username'
        ' FROM proxy p JOIN user u ON p.author_id = u.id'
        ' WHERE delay IS NOT NULL'
        ' ORDER BY created DESC, delay ASC'
    ).fetchall()
    return render_template('blog/home.html', records=records)


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        ip = request.form['ip']
        port = request.form['port']
        delay = request.form['delay']
        error = None

        if not ip:
            error = 'IP is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO proxy (ip, port, delay, author_id)'
                ' VALUES (?, ?, ?, ?)',
                (ip, port, delay, g.user['id'])
            )
            db.commit()
            return redirect(url_for('blog.dashboard'))

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
