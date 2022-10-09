import logging
from flask import current_app
import os
from datetime import datetime
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, session
)
from werkzeug.exceptions import abort

from odk_fieldmap.auth import login_required
from odk_fieldmap.models import (db, Project, Task, User)

bp = Blueprint('project', __name__)


@bp.route('/')
def index():
    projects = Project.query.join(
        User, Project.author_id == User.id).order_by(Project.created)

    if session.get('user_id'):
        tasks = get_tasks_for_user(session['user_id'])
        return render_template('project/index.html', tasks=tasks, projects=projects)
    return render_template('project/index.html', projects=projects)


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    current_app.logger.info("message")
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            user_id = g.user['id']
            project = Project(
                title=title,
                description=description,
                author_id=user_id,
                base_dir=f'/example_files/{title}',
            )
            db.session.add(project)
            db.session.commit()

            # REMOVE LATER
            startingtask = int(request.form['startingtask'])
            lasttask = int(request.form['lasttask'])
            create_tasks(db, title, startingtask, lasttask)

            return redirect(url_for('project.index'))

    return render_template('project/create.html')


def create_tasks(db, title, first, last):
    # this has a bug if project name is the same
    project = db.session.query(Project).where(Project.title == title).first()

    error = None
    if not project:
        error = 'Project cannot be found.'
    if error is not None:
        flash(error)
        return

    task_numbers = range(first, last+1)
    for num in task_numbers:
        task = Task(
            task_number=num,
            project_id=project['id']
        )
        db.session.add(task)
    db.session.commit()


def get_tasks_for_project(project_id):
    tasks = db.session.query(Task).join(
        Project, Task.project_id == Project.id).where(Project.id == project_id)

    return tasks


def get_in_progress_task_numbers(tasks):
    in_progress = []
    for task in tasks.values():
        if task['in_progress']:
            in_progress.append(task['task_number'])
    return in_progress


def get_tasks_for_user(user_id):
    tasks = db.session.query(Task).join(
        Project, Task.project_id == Project.id).where(Task.task_doer == user_id)
    return tasks


def get_project(id, check_author=True):
    project = db.session.query(Project).join(
        User, Project.author_id == User.id).where(Project.id == id).first()

    if project is None:
        abort(404, f"Project id {id} doesn't exist.")

    if check_author and project['author_id'] != g.user['id']:
        abort(403)

    return project


# most recent attempt to download: https://gist.github.com/redlotus/3138bd661ceb02abf1f6
# def get_file_params(full_path, filename):
#     filepath = os.path.abspath(current_app.root_path)+"/../download/"+filename
#     if os.path.isfile(filepath):
#         return filename,"/download/"+filename,os.path.getsize(filepath)
#     with open(filepath, 'w') as outfile:
#         data = load_from_mongo("ddcss","queries",\
#             criteria = {"_id" : ObjectId(filename)}, projection = {'_id': 0})
#         #outfile.write(json.dumps(data[0], default=json_util.default))
#         outfile.write(dumps(data[0]))
#     return filename, "/download/"+filename, os.path.getsize(filepath)
#
# def download(file_id):
# 	(file_basename, server_path, file_size) = get_file_params(file_id)
# 	response = make_response()
# 	response.headers['Content-Description'] = 'File Transfer'
# 	response.headers['Cache-Control'] = 'no-cache'
# 	response.headers['Content-Type'] = 'application/octet-stream'
# 	response.headers['Content-Disposition'] = 'attachment; filename=%s' % file_basename
# 	response.headers['Content-Length'] = file_size
# 	response.headers['X-Accel-Redirect'] = server_path # nginx: http://wiki.nginx.org/NginxXSendfile
#
# 	return response

# todo: make this work
def check_for_task_number(request):
    task_number = request.form['tasknum']
    error = None

    msg = "Attempted post with task number: "+task_number

    if not task_number:
        error = 'Task Number cannot be blank. Please select task again.'

        if error is not None:
            msg = error
            flash(error)
    return task_number


@bp.route('/<int:id>/map', methods=('GET', 'POST'))
def map(id):
    project = get_project(id, False)

    tasks = {}
    task_list = get_tasks_for_project(project['id'])
    for task in task_list:
        tasks[task['task_number']] = task

    msg = ""

    if request.method == 'POST':
        if session.get('user_id'):

            task_number = check_for_task_number(request)
            if task_number:
                matching_tasks = db.session.query(Task).where(
                    Task.project_id == id, Task.task_number == task_number)
                msg = matching_tasks

                db.execute(
                    'UPDATE task SET in_progress = ?, task_doer = ?, last_selected = ?'
                    ' WHERE project_id = ? AND task_number = ?',
                    (1, session.get('user_id'), datetime.now(), id, task_number)
                )
                db.session.commit()

                # extra_actions = request.form.getlist('select_extras')
                # flash(extra_actions)
                # if extra_actions.contains('download'):
                #     new_filename = project['title']+"_task"+task_id+"_qrcode.gif"
                #     full_path = url_for('static', filename='example_files/Partial_Mikocheni/QR_codes/Mikocheni_buildings_198.gif')
                #     flash("Downloading: "+full_path)
                #     return send_from_directory(full_path, filename, as_attachment=True)
                # else:
                #     flash("No download requested.")
                # return redirect(url_for('project.index'))
            in_progress = get_in_progress_task_numbers(tasks)

            return render_template('project/map.html', project=project, tasks=tasks, in_progress=in_progress, msg=in_progress)
        else:
            return redirect(url_for("auth.login"))
    else:
        in_progress = get_in_progress_task_numbers(tasks)

        return render_template('project/map.html', project=project, tasks=tasks, in_progress=in_progress, msg=in_progress)


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    project = get_project(id)

    if request.method == 'POST':
        title = request.form['title']
        desc = request.form['description']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            project = db.session.query(Project).where(Project.id == id).first()
            project.title = title
            project.description = desc
            db.session.commit()

            return redirect(url_for('project.index'))

    return render_template('project/update.html', project=project)


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_project(id)
    project = db.session.query(Project).where(Project.id == id).first()
    db.session.delete(project)
    db.session.commit()

    return redirect(url_for('project.index'))


@bp.route('/<int:id>/release', methods=('POST',))
@login_required
def release(id, task_num):
    task_number = check_for_task_number(request)

    if task_number is None:
        abort(404, f"Task number is required.")

    task = check_task_doer(proj_id, task_num)
    task = db.session.query(Task).where(Task.id == id).first()
    db.session.delete(task)
    db.commit()

    return redirect(url_for('project.index'))


def check_task_doer(proj_id, task_num):
    task = db.session.query(Task).where(
        Task.project_id == proj_id, Task.task_number == task_num).first()

    if task is None:
        abort(404, f"Project id {id} doesn't exist.")

    if check_author and task['task_doer'] != g.user['id']:
        abort(403)

    return task
