# Encrypter Util

Field-TM encrypts the ODK access token & ODK passwords in the database.

Sometimes these must be manually encrypted / decrypted for the database.

This util makes that process easier.

```bash
usage: encrypter.py [-h] [--encrypt] [--decrypt] key value

Encrypt or decrypt string values.

positional arguments:
  key         Encryption key.
  value       Value to encrypt or decrypt.

options:
  -h, --help  show this help message and exit
  --encrypt   Encrypt the value.
  --decrypt   Decrypt the value.
```

> Note the values may need to be quoted, as they often contain special chars.

## Encrypt a value

```bash
docker run -i --rm ghcr.io/hotosm/field-tm/encrypter:latest \
  --encrypt \
  your_encryption_token \
  some_value_to_encrypt
```

## Decrypt a value

```bash
docker run -i --rm ghcr.io/hotosm/field-tm/encrypter:latest \
  --decrypt \
  your_encryption_token \
  some_value_to_encrypt
```
