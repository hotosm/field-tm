"""
Example on how to go through the workflow of creating project, adding app users etc.
"""
from odk2odm import odk_requests

base_url = "https://3dstreetview.org"
aut = ("email", "password")


# Create a project
odk_requests.create_project(
    base_url, aut, project_name="Reetta_example_odk_requests")


# Upload a form for the project
projectId = odk_requests.project_id(
    base_url, aut, projectName="Reetta_example_odk_requests"
)  # get project id for the created project
path2Form = "../odm360_photos_0-1-2.xlsx"  # or the fill photos
odk_requests.create_form(
    base_url, aut, projectId=projectId, path2Form=path2Form)


# Create an app user for the project
odk_requests.create_app_user(
    base_url, aut, projectId
)  # Creates an app user called surveyor


# Give access to (all) app user(s)
odk_requests.give_access_app_users(base_url, aut, projectId)


# Create QR code strings for (all) app user(s)
qr_data_dict = odk_requests.generate_qr_data_dict(
    base_url, aut, projectId
)  # The first values is app user id and second the qr string
