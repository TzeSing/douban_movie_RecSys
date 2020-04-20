# -*- coding: utf-8 -*-

"""
recsys.public.views
~~~~~~~~~~~~~~~~~~~

Public section, including homepage and signup.

:copyright: (c) 2020 by TzeSing.
:license: Apache2, see LICENSE for more details.
"""

import time
from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
    make_response,
    jsonify
)
from flask_login import login_required, login_user, logout_user
from recsys.extensions import login_manager
from recsys.public.forms import LoginForm
from recsys.user.forms import RegisterForm
from recsys.extensions import db
from recsys.user.models import User, Movies, Ratings
from recsys.utils import flash_errors

blueprint = Blueprint("public", __name__, static_folder="../static")


@login_manager.user_loader
def load_user(user_id):
    """Load user by ID."""
    return User.get_by_id(int(user_id))


@blueprint.route("/", methods=["GET", "POST"])
def home():
    """Home page."""
    form = LoginForm(request.form)
    current_app.logger.info("Hello from the home page!")
    # Handle logging in
    if request.method == "POST":
        if form.validate_on_submit():
            login_user(form.user)
            flash("You are logged in.", "success")
            redirect_url = request.args.get("next") or url_for("user.members")
            return redirect(redirect_url)
        else:
            flash_errors(form)
    return render_template("public/home.html", form=form)


@blueprint.route("/logout/")
@login_required
def logout():
    """Logout."""
    logout_user()
    flash("You are logged out.", "info")
    return redirect(url_for("public.home"))


@blueprint.route("/register/", methods=["GET", "POST"])
def register():
    """Register new user."""
    form = RegisterForm(request.form)
    if form.validate_on_submit():
        User.create(username=form.username.data)
        flash("Thank you for registering. You can now log in.", "success")
        return redirect(url_for("public.home"))
    else:
        flash_errors(form)
    return render_template("public/register.html", form=form)


@blueprint.route("/about/")
def about():
    """About page."""
    form = LoginForm(request.form)
    return render_template("public/about.html", form=form)


@blueprint.route("/popular/")
def popular():
    """Popular movie ranks"""
    sql = "select mid, movie_name, t.c from \
     (select ratings.mid, count(mid) as c from ratings group by mid order by c desc limit 10) t \
    JOIN movies on t.mid=movies.id order by t.c desc"
    popular5_movies = db.session.execute(sql)
    return render_template("users/popular.html", popular5_movies=popular5_movies)


@blueprint.route("/movie_info/<mid>")
def movie_info(mid):
    """Movie info Page"""
    sql = "SELECT score, count(uid) as nums FROM ratings WHERE mid={mid} \
           GROUP BY score".format(mid=mid)
    score_per_count = db.session.execute(sql).fetchall()
    score_dict = {1.0: 0, 2.0: 0, 3.0: 0, 4.0: 0, 5.0: 0}
    for (score, count) in score_per_count:
        score_dict[score] = count
    movie_name = db.session.execute(
        "SELECT movie_name FROM movies where id={}".format(mid)).fetchone()[0]
    return render_template("users/movie_info.html", score_dict=score_dict,
                           movie_name=movie_name, mid=mid)


@blueprint.route("/rate_movie/", methods=["POST"])
@login_required
def rate_movie():
    """给电影评分"""
    params = request.get_json()
    username = params['username']
    mid = int(params['mid'])
    score = float(params['score'])

    query = db.session.execute(
        "SELECT id FROM users WHERE username='{}'".format(username))
    uid = query.fetchone()[0]
    rating = Ratings(uid=uid, mid=mid, score=score)
    db.session.add(rating)
    try:
        db.session.commit()
        status = "插入成功"
        return jsonify({'status': status}), 200
    except Exception as e:
        print(e)
        status = "插入失败"
        return jsonify({'status': status}), 404


@blueprint.route("/movie_rec/<string:username>")
@login_required
def movie_rec(username):
    """根据用户username来获取UserCF的推荐结果"""
    sql = "SELECT id FROM users WHERE username='{}'".format(username)
    query = db.session.execute(sql).fetchone()
    uid = query[0]
    sql = "SELECT midrecs FROM userrecs WHERE uid={}".format(uid)
    query = db.session.execute(sql).fetchone()
    recs = query[0]
    mid_recs = [int(i) for i in recs.split(",")]
    movies_recs = []
    for mid in mid_recs:
        sql = "SELECT movie_name FROM movies WHERE id={}".format(mid)
        try:
            movie_name = db.session.execute(sql).fetchone()[0]
            movies_recs.append(movie_name)
        except:
            mid_recs.remove(mid)
    pairs = zip(movies_recs, mid_recs)
    return render_template("users/movie_rec.html", pairs=pairs)


@blueprint.route('/real_time/')
def real_time():
    return render_template("users/real_time.html")


@blueprint.route('/search/', methods=['POST'])
def search():
    """搜索电影"""
    param = request.get_json()
    movie_name = param["movie_name"]
    sql = 'SELECT id FROM movies WHERE movie_name="{}"'.format(movie_name)
    mid = db.session.execute(sql).fetchone()[0]
    return jsonify({'mid': mid})


@blueprint.route('/get_realtime_rec/', methods=['POST'])
def get_realtime_rec():
    """获取实时的电影推荐

    给定uid与mid就能获取到recs
    """
    param = request.get_json()
    username = param['username']
    mid = param['mid']

    sql = "SELECT id FROM users WHERE username='{}'".format(username)
    query = db.session.execute(sql).fetchone()
    uid = query[0]

    # 等待spark streaming计算并写回MySQL
    time.sleep(5)
    sql = "SELECT recs FROM movierecs WHERE uid={} and mid={}".format(uid, mid)
    query = db.session.execute(sql).fetchone()
    recs = query[0]
    recs = recs.split(',')

    movie_name_recs = []
    for mid in recs:
        sql = "SELECT movie_name FROM movies WHERE id={}".format(mid)
        query = db.session.execute(sql).fetchone()
        movie_name_recs.append(query[0])
    return jsonify({'movie_name_recs': movie_name_recs})
