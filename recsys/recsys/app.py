# -*- coding: utf-8 -*-

"""
recsys.app
~~~~~~~~~~~~~~~~~~~

The app module, containing the app factory function.

:copyright: (c) 2020 by TzeSing.
:license: Apache2, see LICENSE for more details.
"""

import logging
import sys

from flask import Flask, render_template
from flask_wtf.csrf import generate_csrf
from recsys import commands, public, user
from recsys.extensions import (
    cache,
    csrf_protect,
    db,
    debug_toolbar,
    flask_static_digest,
    login_manager,
    migrate,
)


def create_app(config_object="recsys.settings"):
    """Create application factory, as explained here: http://flask.pocoo.org/docs/patterns/appfactories/.

    :Args
        config_object: The configuration object to use.
    """
    app = Flask(__name__.split(".")[0])
    app.config.from_object(config_object)
    register_extensions(app)
    register_blueprints(app)
    register_errorhandlers(app)
    register_shellcontext(app)
    register_commands(app)
    configure_logger(app)

    @app.after_request
    def after_request(response):
        # 调用函数生成 csrf_token
        csrf_token = generate_csrf()
        # 通过 cookie 将值传给前端
        response.set_cookie("csrf_token", csrf_token)
        return response
    return app


def register_extensions(app):
    """Register Flask extensions."""
    cache.init_app(app)
    db.init_app(app)
    csrf_protect.init_app(app)
    login_manager.init_app(app)
    debug_toolbar.init_app(app)
    migrate.init_app(app, db)
    flask_static_digest.init_app(app)
    return None


def register_blueprints(app):
    """Register Flask blueprints."""
    app.register_blueprint(public.views.blueprint)
    app.register_blueprint(user.views.blueprint)
    return None


def register_errorhandlers(app):
    """Register error handlers."""

    def render_error(error):
        """Render error template."""
        # If a HTTPException, pull the `code` attribute; default to 500
        error_code = getattr(error, "code", 500)
        return render_template(f"{error_code}.html"), error_code

    for errcode in [401, 404, 500]:
        app.errorhandler(errcode)(render_error)
    return None


def register_shellcontext(app):
    """Register shell context objects."""

    def shell_context():
        """Shell context objects."""
        return {"db": db, "User": user.models.User,
                "Movies": user.models.Movies, "Ratings": user.models.Ratings}

    app.shell_context_processor(shell_context)


def register_commands(app):
    """Register Click commands."""
    app.cli.add_command(commands.test)
    app.cli.add_command(commands.lint)


def configure_logger(app):
    """Configure loggers."""
    handler = logging.StreamHandler(sys.stdout)
    if not app.logger.handlers:
        app.logger.addHandler(handler)
