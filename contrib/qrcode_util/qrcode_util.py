"""Convert between JSON and QRCode formats."""

import sys
import argparse
import base64
import json
import zlib
from io import BytesIO

from PIL import Image
from segno import make as make_qr
from pyzbar.pyzbar import decode as decode_qr


def qr_to_json(qr_code_bytes: bytes):
    """Extract QR code content to JSON."""
    qr_img = Image.open(BytesIO(qr_code_bytes))
    qr_data = decode_qr(qr_img)[0].data

    # Base64/zlib decoded
    decoded_qr = zlib.decompress(base64.b64decode(qr_data))
    odk_json = json.loads(decoded_qr.decode("utf-8"))
    # Output to terminal
    print(odk_json)

def json_to_qr(json_bytes: bytes):
    """Insert JSON content into QR code."""
    json_string = json.loads(json_bytes.decode('utf8').replace("'", '"'))

    # Base64/zlib encoded
    qrcode_data = base64.b64encode(
        zlib.compress(json.dumps(json_string).encode("utf-8"))
    )
    qrcode = make_qr(qrcode_data, micro=False)
    buffer = BytesIO()
    qrcode.save(buffer, kind="png", scale=5)
    qrcode_binary = buffer.getvalue()
    sys.stdout.buffer.write(qrcode_binary)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Encode or decode QR code data."
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write data from STDIN to a QRCode.",
    )
    parser.add_argument(
        "--read",
        action="store_true",
        help="Read QRCode data from STDIN and print to terminal.",
    )

    args = parser.parse_args()

    # Read STDIN data, usage:
    # $ cat file.png | docker run -i --rm ghcr.io/hotosm/field-tm/qrcodes:latest --write
    data_in: bytes = sys.stdin.buffer.read()
    if data_in == b"":
        print("Data must be provided via STDIN.")
        sys.exit(1)

    if args.write:
        json_to_qr(data_in)
    elif args.read:
        qr_to_json(data_in)
    else:
        print("Please provide either --write or --read flag.")    
