#!/usr/bin/env python3
# coding: utf-8
from lastpass import Vault
from onepassword import OnePassword
from getpass import getpass
import json
import subprocess
import base64
import os
import sys
import hashlib
import yaml


def parse_op_item(item):
    uuid = item["uuid"]
    name = item["overview"]["title"]
    fields = item["details"]["fields"]
    username = fields[0]["value"] if len(fields) > 1 and "value" in fields[0] else ""
    password = fields[1]["value"] if len(fields) > 1 and "value" in fields[1] else ""
    note = item["details"]["notesPlain"]
    url = item["overview"]["url"]
    return uuid, name, username, password, url, note


def parse_lp_item(item):
    iid = item.id.decode("utf-8")
    name = item.name.decode("utf-8")
    group = item.group.decode("utf-8")
    username = item.username.decode("utf-8")
    password = item.password.decode("utf-8")
    url = item.url.decode("utf-8")
    note = item.notes.decode("utf-8")
    return iid, group, name, username, password, url, note


def compare_item(op_item, lp_item):
    return parse_op_item(op_item)[1:] == parse_lp_item(lp_item)[2:]


def create_op_item(name, url, username, password, note, vault):
    fields = [
        {"designation": "username", "name": "username", "type": "T", "value": username},
        {"designation": "password", "name": "password", "type": "P", "value": password},
    ]
    payload = (
        base64.urlsafe_b64encode(
            json.dumps({"fields": fields, "notesPlain": note}).encode("utf-8")
        )
        .decode("utf-8")
        .strip("=")
    )
    if url.startswith("http://"):
        url = url.replace("http://", "https://")
    cmd = f"op create item --title {name} --url {url} --vault {vault} Login {payload}"
    result = subprocess.run(cmd.split(), capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


def update_op_item(uuid, title, url, username, password, note):
    cmd = (
        "op edit item {} title={} url={} username={} password={} notesPlain={}".format(
            uuid, title, url, username, password, note
        )
    )
    result = subprocess.run(
        cmd.split(" ", 8), capture_output=True, text=True, check=True
    )
    return result.returncode


def digest_item(metadata):
    m = hashlib.md5()
    m.update("-".join(metadata).encode("utf-8"))
    return m.hexdigest()


def parse_config(filename):
    with open(filename) as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
        return config


if __name__ == "__main__":
    if os.path.exists("config.yaml"):
        config = parse_config("config.yaml")
    else:
        print("can not find config.yaml")
        sys.exit(1)

    if "lastpass" in config:
        username = config["lastpass"]["username"]
        password = config["lastpass"]["password"]
    else:
        username = input("Username: ")
        password = getpass("Password: ")
    otp = input("One Time Password: ")
    op_sessions = [i for i in os.environ.keys() if i.startswith("OP_SESSION_")]
    if op_sessions:
        account = op_sessions[0].split("_")[2]
    else:
        print("no active 1password seesion")
        sys.exit(1)

    lp = Vault.open_remote(username, password, otp)
    op = OnePassword(account=account)

    if "vaultMaps" in config and account in config["vaultMaps"]:
        vaults = config["vaultMaps"][account]
    else:
        vaults = {"All": "Private"}

    items = []
    for v in vaults.values():
        items += op.list_items(vault=v)

    # sync from lp to op
    lp_items = [i for i in lp.accounts if i.password]
    op_items = {}
    for i in items:
        item = op.get_item(i["uuid"])
        op_item_digest = digest_item(parse_op_item(item)[1:])
        op_items[op_item_digest] = item

    for i in lp_items:
        iid, group, name, username, password, url, note = parse_lp_item(i)
        lp_item_digest = digest_item(parse_lp_item(i)[2:])

        if lp_item_digest in op_items:
            # print(f"item {name} already exists on 1password")
            continue

        if group in vaults:
            vault = vaults[group]
        elif "All" in vaults:
            vault = vaults["All"]
        else:
            print(
                f"{name} is in group {group} which is not in whitelist, skip it for now"
            )
            continue
        print(f"create new item {name} in valut {vaults[group]} on 1password")
        create_op_item(name, url, username, password, note, vault)
