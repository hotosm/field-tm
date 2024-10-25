"""Convert a QR Code image in Postgres to a Fernet encrypted odk_token URL.

NOTE since 2024-04-04 database migrations, this will no longer work!
"""

import argparse
import base64
import json
import zlib
from io import BytesIO
from pathlib import Path

from dotenv import load_dotenv

# pip install pillow
from PIL import Image

# apt install libzbar-dev
from pyzbar.pyzbar import decode as decode_qr
from segno import make as make_qr
from sqlalchemy import Column, ForeignKey, Integer, LargeBinary, String
from sqlalchemy.orm import relationship
from sqlalchemy.orm.attributes import InstrumentedAttribute

load_dotenv(Path(__file__).parent.parent / ".env.example")

from app.config import decrypt_value, encrypt_value  # noqa: E402
from app.db.database import Base, get_db  # noqa: E402
from app.db.db_models import DbProject, DbTask  # noqa: E402


class DbQrCode(Base):
    """QR Code."""

    __tablename__ = "qr_code"

    id = Column(Integer, primary_key=True)
    filename = Column(String)
    image = Column(LargeBinary)


class TaskPlusQR(DbTask):
    """Task plus QR code foreign key."""

    qr_code_id = Column(Integer, ForeignKey("qr_code.id"), index=True)
    qr_code = relationship(DbQrCode, cascade="all", single_parent=True)
    if not isinstance(DbTask.odk_token, InstrumentedAttribute):
        odk_token = Column(String, nullable=True)


def odktoken_to_qr():
    """Extract odk_token field from db and convert to QR codes."""
    db = next(get_db())
    projects = db.query(DbProject).all()

    for project in projects:
        project_name = project.slug
        tasks = project.tasks

        for task in tasks:
            odk_token = task.odk_token
            if not odk_token:
                continue

            decrypted_odk_token = decrypt_value(odk_token)
            qr_code_setting = {
                "general": {
                    "server_url": decrypted_odk_token,
                    "form_update_mode": "match_exactly",
                    "basemap_source": "osm",
                    "autosend": "wifi_and_cellular",
                    "metadata_username": "svcfmtm",
                },
                "project": {"name": f"{project_name}"},
                "admin": {},
            }

            # Base64/zlib encoded
            qrcode_data = base64.b64encode(
                zlib.compress(json.dumps(qr_code_setting).encode("utf-8"))
            )
            qrcode = make_qr(qrcode_data, micro=False)
            buffer = BytesIO()
            qrcode.save(buffer, kind="png", scale=5)
            qrcode_binary = buffer.getvalue()
            qrdb = DbQrCode(image=qrcode_binary)
            db.add(qrdb)
            print(f"Added qrcode for task {task.id} to db")
    db.commit()


def qr_to_odktoken():
    """Extract QR codes from db and convert to odk_token field."""
    db = next(get_db())
    tasks = db.query(TaskPlusQR).all()

    for task in tasks:
        if task.qr_code:
            qr_img = Image.open(BytesIO(task.qr_code.image))
            qr_data = decode_qr(qr_img)[0].data

            # Base64/zlib decoded
            decoded_qr = zlib.decompress(base64.b64decode(qr_data))
            odk_token = (
                json.loads(decoded_qr.decode("utf-8"))
                .get("general", {})
                .get("server_url")
            )

            task.odk_token = encrypt_value(odk_token)
            print(f"Added odk token for task {task.id}")
    db.commit()


def encrypt_odk_creds():
    """Encrypt project odk password in the db."""
    db = next(get_db())
    projects = db.query(DbProject).all()

    for project in projects:
        project.odk_central_password = encrypt_value(project.odk_central_password)
        print(f"Encrypted odk password for project {project.id}")
    db.commit()


def decrypt_odk_creds():
    """Decrypt project odk password in the db."""
    db = next(get_db())
    projects = db.query(DbProject).all()

    for project in projects:
        project.odk_central_password = decrypt_value(project.odk_central_password)
        print(f"Encrypted odk password for project {project.id}")
    db.commit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Apply or revert changes to QR codes and odk tokens."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply changes (convert QR codes to odk tokens).",
    )
    parser.add_argument(
        "--revert",
        action="store_true",
        help="Revert changes (convert odk tokens to QR codes).",
    )

    args = parser.parse_args()

    if args.apply:
        qr_to_odktoken()
        encrypt_odk_creds()
    elif args.revert:
        odktoken_to_qr()
        decrypt_odk_creds()
    else:
        print("Please provide either --apply or --revert flag.")
