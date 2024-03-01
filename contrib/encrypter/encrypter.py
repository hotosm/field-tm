"""Convert between JSON and QRCode formats."""

import sys
import argparse
import base64
from cryptography.fernet import Fernet



def get_cipher_suite(key):
    """Cache cypher suite."""
    return Fernet(key)


def encrypt_value(key: str, value: str) -> str:
    """Encrypt value before going to the DB."""
    cipher_suite = get_cipher_suite(key)
    encrypted_password = cipher_suite.encrypt(value.encode("utf-8"))
    return base64.b64encode(encrypted_password).decode("utf-8")


def decrypt_value(key: str, value: str) -> str:
    """Decrypt the database value."""
    cipher_suite = get_cipher_suite(key)
    encrypted_password = base64.b64decode(value.encode("utf-8"))
    decrypted_password = cipher_suite.decrypt(encrypted_password)
    return decrypted_password.decode("utf-8")


def display_value(value: str) -> None:
    """Pretty print the final value."""
    print("")
    print("Value:")
    print("")
    print(value)
    print("")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Encrypt or decrypt string values."
    )
    parser.add_argument(
        "key",
        help="Encryption key.",
    )
    parser.add_argument(
        "value",
        help="Value to encrypt or decrypt.",
    )
    parser.add_argument(
        "--encrypt",
        action="store_true",
        help="Encrypt the value.",
    )
    parser.add_argument(
        "--decrypt",
        action="store_true",
        help="Decrypt the value.",
    )

    args = parser.parse_args()

    if args.encrypt and args.decrypt:
        print("Cannot both encrypt and decrypt at the same time.")
        print("Pass one of either: --encrypt or --decrypt")
        sys.exit(1)

    if args.encrypt:
        result = encrypt_value(args.key, args.value)
        display_value(result)
    elif args.decrypt:
        result = decrypt_value(args.key, args.value)
        display_value(result)
    else:
        print("Please provide either --encrypt or --decrypt flag.")  
