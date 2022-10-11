# Storage for Reetta's old QR code stuff,
# which I'm not sufficiently familiar with to use.


def get_qr_code(base_url, aut, pid, token, admin={}, general=general):
    url = f"{base_url}/v1/key/{token}/projects/{pid}"
    qr_data = {"general": general, "admin": admin}
    qr_data["general"]["server_url"] = url
    qr_data_bytes = json.dumps(qr_data).encode("utf-8")
    qr_data_comp = zlib.compress(qr_data_bytes)
    qr_data_comp_utf = codecs.encode(qr_data_comp, "base64_codec")
    qr_data_comp_str = qr_data_comp_utf.decode("utf-8").replace("\n", "")
    img = qrcode.make(qr_data_comp_str)
    img.save("check_this.png")
    return img, 200


def generate_qr_data_dict(base_url, aut, pid, admin={}, general=general):
    url = f"{base_url}/v1/projects/{pid}/app-users"
    app_users = requests.get(url, auth=aut).json()
    qr_data_dict = {}
    false = False
    true = True
    for app_user in app_users:
        token = app_user["token"]
        app_user_id = app_user["id"]
        url = f"{base_url}/v1/key/{token}/projects/{pid}"
        qr_data = {"general": general, "admin": admin}
        qr_data["general"]["server_url"] = url
        qr_data_bytes = json.dumps(qr_data).encode("utf-8")
        qr_data_comp = zlib.compress(qr_data_bytes)
        qr_data_comp_utf = codecs.encode(qr_data_comp, "base64_codec")
        qr_data_comp_str = qr_data_comp_utf.decode("utf-8").replace("\n", "")
        img = qrcode.make(qr_data_comp_str)
        img.save("MyQRCode1.png")
        qr_data_dict[app_user_id] = qr_data_comp_str

    return (json.dumps(qr_data_dict), 200)


# Test QR settings data
# See here to see all the possible settings: https://docs.getodk.org/collect-import-export/?highlight=configure


def give_access_app_users(base_url, aut, pid, roleId=2):
    """Give all the app-users in the project access to all the forms in that project"""
    url = f"{base_url}/v1/projects/{pid}/forms"
    forms = requests.get(url, auth=aut).json()

    for form in forms:
        formId = form["xmlFormId"]
        url = f"{base_url}/v1/projects/{pid}/app-users"
        app_users = requests.get(url, auth=aut).json()
        for user in app_users:
            kwargs = {"formId": formId, "actorId": user["id"]}
            update_role_app_user(base_url, aut, pid, roleId=roleId, **kwargs)
            # url = f'{base_url}/v1/projects/{pid}/forms/{formId}/assignments/{roleId}/{actorId}'
            # requests.post(url, auth = aut)
    return "Role successfully changed", 200
