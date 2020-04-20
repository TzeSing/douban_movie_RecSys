# -*- coding: utf-8 -*-

"""
recsys.extensions
~~~~~~~~~~~~~~~~~

Extensions module. Each extension is initialized in the app factory located in app.py.

:copyright: (c) 2020 by TzeSing.
:license: Apache2, see LICENSE for more details.
"""

from flask_caching import Cache
from flask_debugtoolbar import DebugToolbarExtension
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_static_digest import FlaskStaticDigest
from flask_wtf.csrf import CSRFProtect

csrf_protect = CSRFProtect()
login_manager = LoginManager()
db = SQLAlchemy()
migrate = Migrate()
cache = Cache()
debug_toolbar = DebugToolbarExtension()
flask_static_digest = FlaskStaticDigest()
