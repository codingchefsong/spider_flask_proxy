import os

from flask import Flask
from flask_uploads import UploadSet, configure_uploads, IMAGES, patch_request_class
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import SubmitField

photos = UploadSet('photos', IMAGES)


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)

    # upload file config
    # app.config['UPLOADED_PHOTOS_DEST'] = os.path.join(os.getcwd(), 'uploads')
    # app.config['UPLOADED_FILES_URL'] = os.path.join(os.getcwd(), 'files')
    # app.config['UPLOADS_DEFAULT_DEST'] = os.path.join(os.getcwd(), 'defdest')
    # app.config['UPLOADS_DEFAULT_URL'] = os.path.join(os.getcwd(), 'defurl')
    APP_ROOT = os.path.dirname(os.path.abspath(__file__))
    app.config['UPLOADED_PHOTOS_DEST'] = os.path.join(APP_ROOT, 'uploads')

    configure_uploads(app, photos)
    patch_request_class(app)  # set maximum file size, default is 16MB

    app.config.from_mapping(
        SECRET_KEY='Ju:kb3?%=o/3%vqo',
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # @app.before_first_request
    # def spider():
    #     from . import proxy_spider_socks
    #     import threading
    #
    #     def job():
    #         with app.app_context():
    #             proxy_spider_socks.run()
    #
    #     thread = threading.Thread(target=job)
    #     thread.start()

    from . import db
    db.init_app(app)

    from . import auth
    app.register_blueprint(auth.bp)

    from . import blog
    app.register_blueprint(blog.bp)
    app.add_url_rule('/', endpoint='index')

    return app


"""
For Linux and Mac:

$ export FLASK_APP=flaskr
$ export FLASK_ENV=development
$ flask run

For Windows cmd, use set instead of export:

> set FLASK_APP=flaskr
> set FLASK_ENV=development
> flask run

Init database
> flask init-db


"""