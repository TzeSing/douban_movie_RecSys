# -*- coding: utf-8 -*-

"""
recsys.user.views
~~~~~~~~~~~~~~~~~

User views.

:copyright: (c) 2020 by TzeSing.
:license: Apache2, see LICENSE for more details.
"""

from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required
from recsys.extensions import db

blueprint = Blueprint("user", __name__, url_prefix="/users",
                      static_folder="../static")


@blueprint.route("/")
@login_required
def members():
    """List members."""
    return render_template("users/members.html")


@blueprint.route('/rate_history/', methods=['POST'])
def rate_history():
    """用户的评分记录"""
    params = request.get_json()
    username = params['username']

    sql = 'SELECT id FROM users WHERE username="{}"'.format(username)
    uid = db.session.execute(sql).fetchone()[0]
    sql = 'SELECT mid, score FROM ratings where uid={}'.format(str(uid))
    mid_score_pairs = db.session.execute(sql).fetchall()
    # unzip
    movies = []
    scores = []
    for pair in mid_score_pairs:
        mid, score = pair
        sql = 'SELECT movie_name FROM movies WHERE id={}'.format(mid)
        try:
            movie = db.session.execute(sql).fetchone()[0]
            movies.append(movie)
            scores.append(score)
        except:
            pass
    return jsonify({'movies': movies, 'scores': scores})
