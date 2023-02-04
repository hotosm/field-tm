## ODK Client

odk_client.py is a command line utility for the ODK Central server. It
exposed many of the REST API calls supported by the server, including
uploading and downloading attachments and submissions.

# Server requests

All of the server specific commands are accessible via the
*--server* command. This command takes a single argument, and can only
access the global data about projects and users.

* --server projects - returns a list of project IDs and the project name

* --server users - returns a list of users IDs and their user name

# Project Requests

Projects contain all the Xforms and attachments for that project. To
access the data for a project, it is necesary to supply the project
ID. That can be retrieved using the above server command. In this
example, 1 is used.

* --id 1 --project forms - returns a list of all the XForms contained
                           in this project
* --id 1 --project app-users - returns a list of all the app users who
                           have access to this project.

# XForm Requests

An XForm has several components. The primary one is the XForm
description itself. In addition to that, there may be additional
attachments, usually a CSV file external data to be used by the
XForm. If an XForm has been used to collect data, then it has
submissions for that XForm. These can be downloaded as a CSV file.

To access the data for an XForm, it is necesary to supply the project
ID and the XForm ID. The XForm ID can be retrieced using the above
project command.

* --id 1 --form formid --xform attachments - returns a list of all the
                       attachments for this XForm
* --id 1 --form formid -x download file1, file2,etc... - download the
                       specified attachments for this XForm
* --id 1 --form formid --xform submissions - returns a list of all the
                       submissions for this XForm
* --id 1 --form formid --xform csv - returns the data for the submissions
                       submissions for this XForm
* --id 1 --form formid --xform upload file1,file2,.. - upload
                       attachments for this XForm

# Create a new XForm, and upload these two attachments

These two attachements are input for *select_from_file* in the survey
sheet. For odkconvert, they are usually a list of municipalities and
towns. 

	./odk_client.py --id 4 --form waterpoints --xform create XForms/waterpoints.xml XForms/towns.csv XForms/municipality.csv

# App-user Requests

## Create a new app-user for a project
	./odk_client.py --appuser create --id 4 ---form waterpoints foobar

## create a QR code for the app-user to access ODK Central
	./odk_client.py -i 4 -f waterpoints -a qrcode -u 'jhAbIwHmYCBObnR45l!I3yi$LbCL$q$saJHkDvgwgtKs2F6sso3eepySJ5tyyyAX'

## Delete an app-user from a project
	./odk_client.py --appuser delete --id 4 378

## List all app-users for a project
	./odk_client.py  --id 4 --form waterpoints --project app-users

## Generate a QR code for this app-user for this project
	./odk_client.py -a qrcode -i 4 foobar -f waterpoints -u 'nWYLS1HJ...XDFe'

# Bulk operations

Some commands require multiple queries to ODK Central, and are mostly
limited to the app-users for a project.

## Generate QRcodes for all registered app-users
	./odk_client.py --id 4 --bulk qrcodes --form waterpoints
which generates a png file for each app-user, limited to that
project. 

