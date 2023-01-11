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

import json
import logging
import os
import posixpath
import zipfile
from datetime import datetime
from flask import (Blueprint, current_app, flash, g, redirect, render_template,
                   request, session, url_for, send_file)
from werkzeug.exceptions import abort

from src.web.auth import login_required
from src.web.models import DisplayProject, UITask, UITaskHistory

# api
import requests

bp = Blueprint("project", __name__)
base_url = os.getenv("API_URL")

grid_filename = "grid.geojson"


@bp.route("/")
def index():
    session["open_task_id"] = -1
    session['project_id'] = None
    try:
        with requests.Session() as s:
            response = s.get(f"{base_url}/projects/?skip=0&limit=100")
            if response.status_code == 200:
                api_projects = response.json()
                return render_template("project/index.html", projects=api_projects)

    except Exception as e:
        flash(e)

    # if session.get("user_id"):
        # tasks = get_tasks_for_user(session["user_id"])
        # return render_template("project/index.html", tasks=tasks, projects=ui_projects)
    return render_template("project/index.html")


@bp.route("/create", methods=("GET", "POST"))
@login_required
def create():
    current_app.logger.info("message")

    if request.method == "POST":
        locale = request.form["locale"]
        name = request.form["name"]
        short_description = request.form["short_description"]
        description = request.form["description"]
        instructions = request.form["instructions"]
        per_task_instructions = request.form['per_task_instructions']

        error = None

        if not locale:
            error = "Locale is required."
        if not name:
            error = "Project Name is required."
        if not short_description:
            error = "Short description is required."
        if not description:
            error = "Description is required."
        if not instructions:
            error = "Instructions is required."
        if not per_task_instructions:
            error = "Per task instructions are required."

        if error is not None:
            flash(error)
        else:
            try:
                with requests.Session() as s:
                    response = s.post(
                        f"{base_url}/projects/beta/create_project",
                        json={'author': {
                            "username": session["username"],
                            "id": session['user_id']
                        },
                            "project_info": {
                                "locale": locale,
                                "name": name,
                                "short_description": short_description,
                                "description": description,
                                "instructions": instructions,
                                "per_task_instructions": per_task_instructions
                        }
                        })
                    if response.status_code == 200:
                        session['project_in_progress'] = response.json()
                        return redirect(url_for(".upload_project_zip"))

            except Exception as e:
                if response:
                    error = f"Response code: {response.status_code} -- {response.json()} -- Project Creation failed due to {e}"
                else:
                    error = f"Project Creation failed due to {e}"

            if (error):
                current_app.logger.info(error)
                flash(error)

    return render_template("project/create.html")


@bp.route("/upload", methods=("GET", "POST"))
@login_required
def upload_project_zip():
    current_app.logger.info("message")
    project_in_progress = session['project_in_progress']

    if not project_in_progress:
        redirect(url_for("project/index.html"))

    if request.method == "POST":
        project_id = request.form["project_id"]
        project_name_prefix = request.form["project_name_prefix"]
        task_type_prefix = request.form["task_type_prefix"]

        error = None

        if not project_id:
            error = "Project ID is required."
        if not project_name_prefix:
            error = "Project Name Prefix is required."
        if not task_type_prefix:
            error = "Task Type Prefix is required."

        if "files" in request.files:
            current_app.logger.info(request.files)
            upload_files = request.files.getlist("files")
            current_app.logger.info(upload_files)
            # If the user does not select a file, the browser submits an
            # empty file without a filename.
            if not upload_files:
                error = "No selected file"
            elif len(upload_files) > 1:
                error = "Expecting 1 file"

            file = upload_files[0].read()
        else:
            error = "No file part"

        if error is not None:
            flash(error)
        else:
            try:
                with requests.Session() as s:
                    current_app.logger.info(
                        f'Attempting the post with: {file}')

                    response = s.post(
                        f'{base_url}/projects/beta/{project_id}/upload_zip?project_name_prefix={project_name_prefix}&task_type_prefix={task_type_prefix}',
                        files={'file': file}
                    )
                    current_app.logger.info(f'response: {response.json()}')
                    if response:
                        current_app.logger.info(response.request)

                        if response.status_code == 200:
                            return render_template("project/index.html")
                        else:
                            error = response.text

            except Exception as e:
                if response:
                    error = f"Response code: {response.status_code} -- {response.json()} -- Project Creation failed due to {e}"
                else:
                    error = f"Project Creation failed due to {e}"

            if (error):
                flash(error)

    return render_template("project/upload.html", project_id=project_in_progress['id'])


@bp.route("/<int:id>/map", methods=("GET", "POST"))
@login_required
def map(id):
    if request.method == "POST":
        pass
    else:
        return render_map_by_project_id(id)


@bp.route("/<int:task_uid>/update_task_status", methods=("GET", "POST"))
def update_task_status(task_uid):
    project = session['project_id']

    if project:
        error = None
        task = None

        if request.method == "POST":
            new_status = request.form["updateButton"]
            try:
                with requests.Session() as s:
                    response = s.post(
                        f"{base_url}/tasks/{task_uid}/new_status/{new_status}",
                        json={
                            "username": session["username"],
                            "id": session['user_id']
                        })
                    if response.status_code == 200:
                        task = response.json()
                        session["open_task_id"] = task_uid
                    else:
                        error = response.text

            except Exception as e:
                error = e
        else:
            try:
                with requests.Session() as s:
                    response = s.get(
                        f"{base_url}/tasks/{task_uid}")
                    if response.status_code == 200:
                        task = response.json()
                        return f'<pre>{json.dumps(task, indent=2)}</pre>'
                    else:
                        error = response.text

            except Exception as e:
                error = e
        # TODO This hardcoding is a horrible idea
        if error:
            flash(error)
        return redirect(url_for(".map", id=project))
    else:
        return render_template("project/index.html")


def render_map_by_project_id(id):
    try:
        with requests.Session() as s:
            response = s.get(f"{base_url}/projects/{id}")

            if response.status_code == 200:
                project = response.json()
                session['project_id'] = project['id']

                project_id = project['id']
                project_name = project['project_info'][0]['name']
                project_outline = project['outline_geojson']

                tasks = []
                for task in project['project_tasks']:
                    ui_task = UITask()
                    ui_task.status = task['task_status_str']
                    ui_task.feature_id = task['project_task_index']
                    ui_task.name = task['project_task_name']
                    ui_task.outline = task['outline_geojson']
                    ui_task.uid = task['id']
                    ui_task.qr_code = task['qr_code_in_base64']
                    if task['locked_by_uid']:
                        ui_task.locked_by_name = task['locked_by_username']
                        ui_task.locked_by_uid = task['locked_by_uid']
                    else:
                        ui_task.locked_by_name = ""
                        ui_task.locked_by_uid = -1
                    ui_task.centroid = task['outline_centroid']
                    ui_task.centroid_lat = task['outline_centroid']['geometry']['coordinates'][0]
                    ui_task.centroid_long = task['outline_centroid']['geometry']['coordinates'][1]
                    ui_task.task_history = []

                    for history in task['task_history']:
                        task_history = UITaskHistory()
                        task_history.date = history['action_date']
                        task_history.action_str = history['action_text']
                        ui_task.task_history.append(task_history)

                    tasks.append(ui_task)

                open_task_id = session["open_task_id"]
                session["open_task_id"] = -1

                return render_template(
                    "project/map.html",
                    project_id=project_id,
                    project_name=project_name,
                    project_outline=project_outline,
                    tasks=tasks,
                    userid=session.get("user_id"),
                    open_task_id=open_task_id,
                    # userid=g.user["id"]
                )
    except Exception as e:
        flash(e)

    return redirect(url_for("project.index"))


# @bp.route("/<int:id>/update", methods=("GET", "POST"))
# @login_required
# def update(id):
#     project = get_project(id)

#     if request.method == "POST":
#         title = request.form["title"]
#         desc = request.form["description"]
#         error = None

#         if not title:
#             error = "Title is required."

#         if error is not None:
#             flash(error)
#         else:
#             project = db.session.query(Project).where(Project.id == id).first()
#             project.title = title
#             project.description = desc
#             db.session.commit()

#             return redirect(url_for("project.index"))

#     return render_template("project/update.html", project=project)


# @bp.route("/<int:id>/delete", methods=("POST",))
# @login_required
# def delete(id):
#     # get_project(id)
#     project = db.session.query(Project).where(Project.id == id).first()
#     db.session.delete(project)
#     db.session.commit()

#     return redirect(url_for("project.index"))


# @bp.route("/<int:id>/release", methods=("POST",))
# @login_required
# def release(proj_id, feature_id):
#     # feature_id = check_for_feature_id(request)

#     if feature_id is None:
#         abort(404, f"Task number is required.")

#     task = check_task_doer(proj_id, feature_id)
#     task = db.session.query(Task).where(Task.id == id).first()
#     db.session.delete(task)
#     db.commit()

#     return redirect(url_for("project.index"))


# def check_task_doer(proj_id, feature_id):
#     task = (
#         db.session.query(Task)
#         .where(Task.project_id == proj_id, Task.feature_id == feature_id)
#         .first()
#     )

#     if task is None:
#         abort(404, f"Project id {id} doesn't exist.")

#     if check_author and task["task_doer"] != g.user["id"]:
#         abort(403)

#     return task
