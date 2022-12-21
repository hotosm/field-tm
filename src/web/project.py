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
from src.web.models import DisplayProject, Project, Task, FrontendTaskStatus, User, db

# api
import requests

bp = Blueprint("project", __name__)
base_url =os.getenv("API_URL")

grid_filename = "grid.geojson"


@bp.route("/")
def index():
    try:
        with requests.Session() as s:
            response = s.get(f"{base_url}/projects/?skip=0&limit=100")
            ui_projects = []
            if response.status_code == 200:
                api_projects = response.json()

                for project in api_projects:
                    project_info = project['project_info'][0]
                    # ui_project = DisplayProject(
                    #     id = project['id'],
                    #     author_id = project['author']['id'],
                    #     author_username = project['author']['username'],
                    #     title=project_info['name'],
                    #     description=project_info['short_description'],
                    #     # location=f'{project['city']},{project['country']}',
                    # )
                    # ui_projects.append(ui_project)
            return render_template("project/index.html", projects=api_projects)

    except Exception as e:
        flash(e)
    # projects = Project.query.join(User, Project.author_id == User.id).order_by(
    #     Project.created
    # )

    if session.get("user_id"):
        tasks = get_tasks_for_user(session["user_id"])
        return render_template("project/index.html", tasks=tasks, projects=ui_projects)
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
                                "locale":locale,
                                "name":name,
                                "short_description":short_description,
                                "description":description,
                                "instructions":instructions,
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
                    current_app.logger.info(f'Attempting the post with: {file}')
                    
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
                            error = response.json()

            except Exception as e:
                if response:
                    error = f"Response code: {response.status_code} -- {response.json()} -- Project Creation failed due to {e}"
                else:
                    error = f"Project Creation failed due to {e}"
            
            if (error):
                flash(error)

    return render_template("project/upload.html", project_id=project_in_progress['id'])

def get_qr_file(title, task_id):
    project_folder = get_project_folder(title)
    qr_folder_name = current_app.config["QR_CODE_FOLDER_NAME"]
    file_name = f'buildings_{task_id}.gif'
    return os.path.join(project_folder, qr_folder_name, file_name)

def get_project_folder(title):
    static_folder_path = current_app.config["STATIC_FOLDER"]
    upload_folder_name = current_app.config["PROJECTS_UPLOAD_FOLDER_NAME"]
    return os.path.join(static_folder_path, upload_folder_name, title)


def get_relative_project_path(title):
    upload_folder_name = current_app.config["PROJECTS_UPLOAD_FOLDER_NAME"]
    return posixpath.join(upload_folder_name, title)

def get_project_file(request, form_field_name):
    if form_field_name not in request.files:
        return "No file part"
    current_app.logger.info(request.files)
    upload_files = request.files.getlist(form_field_name)
    current_app.logger.info(upload_files)
    # If the user does not select a file, the browser submits an
    # empty file without a filename.
    if not upload_files:
        return "No selected file"
    elif len(upload_files) > 1:
        return "Expecting 1 file"

    file = upload_files[0]
    full_path = get_project_folder(request.form["title"])
    if not os.path.isdir(full_path):
        os.makedirs(full_path)
    else:
        return "A project directory with this name already exists"

    file_like_object = file.stream._file
    return file_like_object
    # zipfile_ob = zipfile.ZipFile(file_like_object)
    # zipfile_ob.extractall(full_path)
    # zipfile_ob.close()

    # flash("Upload succeeded")
    # return None


def get_geojson(title):
    project_path = get_project_folder(title)
    full_path = os.path.join(project_path, grid_filename)

    file = open(full_path)
    data = json.load(file)

    return data


def get_task_ids_from_geojson(title):
    data = get_geojson(title)
    task_ids = []
    for feature in data["features"]:
        task_ids.append(feature["properties"]["id"])
    return task_ids


def create_tasks(title):
    project = db.session.query(Project).where(Project.title == title).first()

    error = None
    if not project:
        raise ValueError("Project cannot be found.")

    task_ids = get_task_ids_from_geojson(title)
    for num in task_ids:
        task = Task(feature_id=num, project_id=project["id"])
        db.session.add(task)
    db.session.commit()


def rollback_project_creation(title, error):
    # delete project
    # project = db.session.query(Project).where(Project.title == title).first()
    # db.session.delete(project)

    # # delete tasks
    # tasks = db.session.query(Task).where(Task.project_id == project.id)
    # for task in tasks:
    #     db.session.delete(task)

    # delete folder
    pass


def get_tasks_for_project(project_id):
    tasks = (
        db.session.query(Task)
        .join(Project, Task.project_id == Project.id)
        .where(Project.id == project_id)
    )
    return tasks

def get_task_by_id(project_id, task_id):
    tasks = (
        db.session.query(Task)
        .join(Project, Task.project_id == Project.id)
        .where(Project.id == id)
        .where(Task.feature_id == task_id)
        .first()
    )
    return tasks

def get_tasks_for_user(user_id):
    tasks = (
        db.session.query(Task)
        .join(Project, Task.project_id == Project.id)
        .where(Task.task_doer == user_id)
    )
    return tasks


def get_project(id, check_author=True):
    project = (
        db.session.query(Project)
        .join(User, Project.author_id == User.id)
        .where(Project.id == id)
        .first()
    )

    if project is None:
        abort(404, f"Project id {id} doesn't exist.")

    if check_author and project["author_id"] != g.user["id"]:
        abort(403)

    return project

def check_for_feature_id(request):
    feature_id = request.form["tasknum"]
    error = None

    #msg = "Attempted post with task number: " + feature_id
    if not feature_id:
        error = "Task Number cannot be blank. Please select task again."

        if error is not None:
            msg = error
            flash(error)
    return feature_id

def is_valid_status_change(task, new_status):
    if task.status is FrontendTaskStatus.available:
        return (new_status == FrontendTaskStatus.unavailable)
    elif task.status is FrontendTaskStatus.unavailable:
        has_permission = session.get("user_id") == task.task_doer
        return has_permission and (new_status == FrontendTaskStatus.available or new_status == FrontendTaskStatus.ready_for_validation)
    elif task.status is FrontendTaskStatus.ready_for_validation:
        return False
    return False

# Get returns map of a project dispalying all tasks. 
# Post can either include a qrcode to be downloaded, or a new status for a particular task.
@bp.route("/<int:id>/map", methods=("GET", "POST"))
def map(id):
    if request.method == "POST":
        user_id = session.get("user_id")
        if user_id:
            task_id = request.form["taskid"]
            qrcode = request.form["qrcode"]
            error = None

            if not task_id:
                error = "Task ID is required."
            elif (qrcode == 'yes'):
                try:
                    project = get_project(id, False)
                    return send_file(get_qr_file(project['title'], task_id), as_attachment=True)

                except Exception as e:
                    error = f"Download failed for {qrcode} due to {e}"
                    flash(error)
                    return render_map_by_project_id(id)
            
            new_status = request.form["newstatus"]
            if not new_status:
                error = "New status is required."
                
            if error is None:
                try:
                    matching_task = db.session.query(Task).where(
                        Task.id == task_id
                    ).first()

                    if not matching_task:
                        error = "Task cannot be found."
                    elif not is_valid_status_change(matching_task, new_status):
                        error = "Status change is not valid."
                    else:
                        matching_task.status = new_status
                        matching_task.task_doer = user_id
                        db.session.commit()
                except Exception as e:
                    error = f"Database query or update failed with error: {e}"
                        
            if error is not None:
                flash(error)
            return render_map_by_project_id(id)
        else:
            return redirect(url_for("auth.login"))
    else:
        return render_map_by_project_id(id)

class UITask:
    status: str
    feature_id: int 
    name: str
    qr_code: bytes
    outline: str
    uid: int

def render_map_by_project_id(id):
    try:
        with requests.Session() as s:
            response = s.get(f"{base_url}/projects/{id}")
            
            if response.status_code == 200:
                project = response.json()
                project_id = project['id']
                project_name = project['project_info'][0]['name']
                project_outline = project['outline_json']

                current_app.logger.info(project_id)
                current_app.logger.info(project_outline)
                current_app.logger.info(project_name)

                tasks = []
                for task in project['project_tasks']:
                    
                    ui_task = UITask()
                    ui_task.status = task['task_status']
                    ui_task.feature_id = task['project_task_index']
                    ui_task.name = task['project_task_name']
                    ui_task.outline = task['outline_json']
                    ui_task.uid = task['id']
                    
                    current_app.logger.info(ui_task)
                    tasks.append(ui_task)
                
                current_app.logger.info(len(tasks))

                return render_template(
                        "project/map.html", 
                        project_id=project_id,
                        project_name=project_name,
                        project_outline=project_outline, 
                        tasks=tasks,
                        userid=session.get("user_id")
                    )
    except Exception as e:
        flash(e)

    return redirect(url_for("project.index"))

def task_by_feature_id(tasks):
    task_dict = {}
    for task in tasks:
        status = {"value":str(task["status"].name), "label":str(task["status"].value)}

        task_dict[task["feature_id"]] = {
            "id": task["id"],
            "feature_id": task["feature_id"],
            "task_doer": task["task_doer"],
            "status": status,
        }
    return task_dict

@bp.route("/<int:id>/update", methods=("GET", "POST"))
@login_required
def update(id):
    project = get_project(id)

    if request.method == "POST":
        title = request.form["title"]
        desc = request.form["description"]
        error = None

        if not title:
            error = "Title is required."

        if error is not None:
            flash(error)
        else:
            project = db.session.query(Project).where(Project.id == id).first()
            project.title = title
            project.description = desc
            db.session.commit()

            return redirect(url_for("project.index"))

    return render_template("project/update.html", project=project)


@bp.route("/<int:id>/delete", methods=("POST",))
@login_required
def delete(id):
    get_project(id)
    project = db.session.query(Project).where(Project.id == id).first()
    db.session.delete(project)
    db.session.commit()

    return redirect(url_for("project.index"))


@bp.route("/<int:id>/release", methods=("POST",))
@login_required
def release(proj_id, feature_id):
    feature_id = check_for_feature_id(request)

    if feature_id is None:
        abort(404, f"Task number is required.")

    task = check_task_doer(proj_id, feature_id)
    task = db.session.query(Task).where(Task.id == id).first()
    db.session.delete(task)
    db.commit()

    return redirect(url_for("project.index"))


def check_task_doer(proj_id, feature_id):
    task = (
        db.session.query(Task)
        .where(Task.project_id == proj_id, Task.feature_id == feature_id)
        .first()
    )

    if task is None:
        abort(404, f"Project id {id} doesn't exist.")

    if check_author and task["task_doer"] != g.user["id"]:
        abort(403)

    return task
