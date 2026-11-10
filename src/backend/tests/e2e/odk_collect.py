"""A headless stand-in for ODK Collect, speaking OpenRosa to ODK Central.

It makes the same requests the app makes: read the settings QR, list and
download the form and its entity lists, then send a submission. It does not
evaluate XPath, so callers fill in the form's calculated fields themselves.
"""

import csv
import json
import zlib
from base64 import b64decode
from dataclasses import dataclass
from io import StringIO
from urllib.parse import urlsplit, urlunsplit
from uuid import uuid4
from xml.etree import ElementTree

import httpx
from defusedxml.ElementTree import fromstring

from app.config import settings

OPENROSA_HEADERS = {"X-OpenRosa-Version": "1.0"}
XFORMS_NS = "{http://www.w3.org/2002/xforms}"
FORM_LIST_NS = "{http://openrosa.org/xforms/xformsList}"
MANIFEST_NS = "{http://openrosa.org/xforms/xformsManifest}"
JR_TEMPLATE = "{http://openrosa.org/javarosa}template"


@dataclass
class CollectForm:
    """A form as Collect stores it after "Download form"."""

    form_id: str
    xform: bytes
    entity_lists: dict[str, list[dict]]


def settings_from_qr(qr_data: str) -> dict:
    """Decode the Collect settings QR payload, as Collect does on scan."""
    return json.loads(zlib.decompress(b64decode(qr_data)))


def _via_internal_central(url: str) -> str:
    """Send a public Central URL to the internal service, keeping its path.

    The test stack has no proxy, so the public hostname in the QR code and in
    Central's download links does not resolve from inside the backend.
    """
    internal = urlsplit(str(settings.ODK_CENTRAL_URL))
    public = urlsplit(url)
    return urlunsplit(public._replace(scheme=internal.scheme, netloc=internal.netloc))


def _find_text(element, path: str) -> str:
    return element.findtext(path, default="").strip()


class HeadlessCollect:
    """One configured Collect project, bound to an app user's server URL."""

    def __init__(self, server_url: str):
        """Configure from the `server_url` in the project QR code."""
        self.server_url = server_url.rstrip("/")

    async def _get(self, client: httpx.AsyncClient, url: str) -> httpx.Response:
        response = await client.get(
            _via_internal_central(url), headers=OPENROSA_HEADERS
        )
        response.raise_for_status()
        return response

    async def download_form(self) -> CollectForm:
        """Fetch the only listed form, plus the CSV entity lists it uses."""
        async with httpx.AsyncClient() as client:
            form_list = fromstring(
                (await self._get(client, f"{self.server_url}/formList")).content
            )
            [xform_entry] = form_list.findall(f"{FORM_LIST_NS}xform")
            xform = await self._get(
                client, _find_text(xform_entry, f"{FORM_LIST_NS}downloadUrl")
            )
            manifest = fromstring(
                (
                    await self._get(
                        client, _find_text(xform_entry, f"{FORM_LIST_NS}manifestUrl")
                    )
                ).content
            )
            entity_lists = {}
            for media_file in manifest.findall(f"{MANIFEST_NS}mediaFile"):
                filename = _find_text(media_file, f"{MANIFEST_NS}filename")
                if not filename.endswith(".csv"):
                    continue
                url = _find_text(media_file, f"{MANIFEST_NS}downloadUrl")
                csv_text = (await self._get(client, url)).text
                entity_lists[filename] = list(csv.DictReader(StringIO(csv_text)))

        return CollectForm(
            form_id=_find_text(xform_entry, f"{FORM_LIST_NS}formID"),
            xform=xform.content,
            entity_lists=entity_lists,
        )

    async def submit(self, instance: ElementTree.Element) -> None:
        """Send a filled-in instance, as Collect does on "Send"."""
        xml = ElementTree.tostring(instance, encoding="utf-8", xml_declaration=True)
        async with httpx.AsyncClient() as client:
            response = await client.post(
                _via_internal_central(f"{self.server_url}/submission"),
                headers=OPENROSA_HEADERS,
                files={"xml_submission_file": ("submission.xml", xml, "text/xml")},
            )
        response.raise_for_status()


def _without_namespaces(element) -> ElementTree.Element:
    """Copy an instance node the way Collect writes it: plain names, no templates."""
    copy = ElementTree.Element(
        element.tag.removeprefix(XFORMS_NS),
        {k: v for k, v in element.attrib.items() if not k.startswith("{")},
    )
    copy.text = element.text
    for child in element:
        if JR_TEMPLATE not in child.attrib:
            copy.append(_without_namespaces(child))
    return copy


def new_instance(form: CollectForm, answers: dict[str, str]) -> ElementTree.Element:
    """Start a blank instance of the form and fill in the given answers.

    Answer keys are paths below the instance root, like `survey/category`.
    A missing path raises, so a renamed form field fails the test loudly.
    """
    model_instance = fromstring(form.xform).find(
        f".//{XFORMS_NS}model/{XFORMS_NS}instance"
    )
    instance = _without_namespaces(model_instance[0])
    instance.find("meta/instanceID").text = f"uuid:{uuid4()}"
    for path, value in answers.items():
        field = instance.find(path)
        if field is None:
            raise KeyError(f"Form {form.form_id} has no field '{path}'")
        field.text = value
    return instance
