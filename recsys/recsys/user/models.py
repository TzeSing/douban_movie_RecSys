# -*- coding: utf-8 -*-

"""
recsys.user.models
~~~~~~~~~~~~~~~~~~

User models.

:copyright: (c) 2020 by TzeSing.
:license: Apache2, see LICENSE for more details.
"""

from flask_login import UserMixin
from recsys.database import (
    Column,
    Model,
    SurrogatePK,
    db,
)
from sqlalchemy.dialects.mysql import DOUBLE


class User(UserMixin, SurrogatePK, Model):
    """A user of the app."""

    __tablename__ = "users"
    username = Column(db.String(80), unique=True, nullable=False)

    def __init__(self, username, **kwargs):
        """Create instance."""
        db.Model.__init__(self, username=username, **kwargs)

    def __repr__(self):
        """Represent instance as a unique string."""
        return "<User({!r})>".format(self.username)


class Movies(SurrogatePK, Model):
    """Movies table"""

    __tablename__ = "movies"
    movie_name = Column(db.String(254))

    def __init__(self, movie_name, **kwargs):
        """Create instance."""
        db.Model.__init__(self, movie_name=movie_name, **kwargs)

    def __repr__(self):
        """Represent instance as a unique string."""
        return "<Movies({!r})>".format(self.movie_name)


class Ratings(SurrogatePK, Model):
    """Ratings table"""

    __tablename__ = "ratings"
    uid = Column(db.Integer, nullable=False)
    mid = Column(db.Integer, nullable=False)
    score = Column(DOUBLE, nullable=False)

    def __repr__(self):
        """Represent instance as a unique string."""
        return "<Ratings({},{},{})>".format(self.uid, self.mid, self.score)
