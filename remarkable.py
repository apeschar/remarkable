#!/usr/bin/env nix-shell
#!nix-shell -p "python3.withPackages (ps: [ps.requests])"
#!nix-shell -i python

import json
import subprocess
from argparse import ArgumentParser
from base64 import b64encode
from pathlib import Path
from uuid import uuid4

import requests


def make_parser():
    parser = ArgumentParser()
    subparsers = parser.add_subparsers(required=True)

    parser_login = subparsers.add_parser("login")
    parser_login.set_defaults(func=cmd_login)
    parser_login.add_argument(
        "--code",
        "-c",
        required=True,
        help="code generated via https://my.remarkable.com/#desktop",
    )

    parser_token = subparsers.add_parser("token")
    parser_token.set_defaults(func=cmd_token)

    parser_upload = subparsers.add_parser("upload")
    parser_upload.set_defaults(func=cmd_upload)
    parser_upload.add_argument("--file", "-f", required=True)

    return parser


def main():
    args = make_parser().parse_args()
    args.func(args)


def cmd_login(args):
    response = requests.post(
        "https://webapp.cloud.remarkable.com/token/json/2/device/new",
        json={
            "code": args.code,
            "deviceID": str(uuid4()),
            "deviceDesc": "desktop-linux",
        },
    )
    response.raise_for_status()
    Path("device-token").write_text(response.text.strip())


def cmd_token(args):
    print(get_user_token())


def cmd_upload(args):
    data = Path(args.file).read_bytes()

    mime_type = (
        subprocess.check_output(["file", "--brief", "--mime-type", "-"], input=data)
        .decode()
        .strip()
    )

    meta = {
        "parent": "",
        "file_name": Path(args.file).name,
    }

    user_token = get_user_token()

    response = requests.post(
        "https://web.cloud.remarkable.com/doc/v2/files",
        headers={
            "Content-Type": mime_type,
            "Authorization": "Bearer %s" % user_token,
            "Rm-Meta": b64encode(json.dumps(meta).encode()).decode(),
        },
        data=data,
    )
    response.raise_for_status()


def get_user_token():
    response = requests.post(
        "https://webapp.cloud.remarkable.com/token/json/2/user/new",
        headers={
            "Authorization": "Bearer %s" % Path("device-token").read_text().strip()
        },
    )
    response.raise_for_status()
    return response.text.strip()


if __name__ == "__main__":
    main()
