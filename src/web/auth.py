# Copyright (c) 2020, 2021, 2022 Humanitarian OpenStreetMap Team
# This file is part of FMTM.
#
#     FMTM is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     FMTM is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with FMTM.  If not, see <https:#www.gnu.org/licenses/>.
#

import os
import functools
from flask import (Blueprint, flash, g, redirect, render_template, request,
                   session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

# api
import requests

bp = Blueprint("auth", __name__, url_prefix="/auth")
base_url = os.getenv("API_URL")


def ping(url):
    try:
        request = requests.get(url, verify=False)
        is_up = request.status_code == 200
        print(f'{url}, up_status={is_up}')
        return request
    except Exception as e:
        print(f'Error thrown: {e}')
        return e


class User:
    def __init__(self, id, username):
        self.id = id
        self.username = username


@bp.route("/register", methods=("GET", "POST"))
def register():
    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]
        error = None

        if not username:
            error = "Username is required."
        elif not password:
            error = "Password is required."

        if error is None:
            try:
                with requests.Session() as s:
                    response = s.post(
                        f"{base_url}/users/", json={'username': username, 'password': password})
                    if response.status_code == 200:
                        return redirect(url_for("auth.login"))

                    elif response.status_code == 400:
                        error = "Username already registered."
            except Exception as e:
                error = f"Registration failed due to {e}"
        flash(error)
    return render_template("auth/register.html")


@bp.route("/login", methods=("GET", "POST"))
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        error = None

        if not username:
            error = "Username is required."
        elif not password:
            error = "Password is required."

        if error is None:
            try:
                with requests.Session() as s:
                    response = s.post(
                        f"{base_url}/login/", json={'username': username, 'password': password})
                    if response.status_code == 200:
                        response_dict = response.json()

                        user_id = response_dict.get('id')
                        username = response_dict.get('username')

                        if user_id and username:
                            session.clear()
                            session["user_id"] = user_id
                            session["username"] = username
                            return redirect(url_for("index"))
                        else:
                            error = f"Response was successful but everything is not well. See: {response_dict}"

                    elif response.status_code == 400:
                        error = "Login failed."
            except Exception as e:
                error = f"Login failed due to {e}"

        flash(error)

    return render_template("auth/login.html")


@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get("user_id")

    if user_id is None:
        g.user = None
    else:
        g.user = User(user_id, session["username"])


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("auth.login"))
        return view(**kwargs)

    return wrapped_view
