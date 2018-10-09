import json
import requests
import sys
import time

from argparse import ArgumentParser
from collections import deque
from os.path import isfile
from tabber import Tabber


def _argparse():
    arg_parse = ArgumentParser(description="Crawl last.fm for finnish users, given a seed person or a reference to a "
                                           "file containing one seed name per line. Either a seed name or a seed file "
                                           "is required")
    arg_parse.add_argument("api_key", type=str,
                           help="last.fm api key to use for crawling.")
    arg_parse.add_argument("-n", "--name", type=str, default=None,
                           help="Seed name for crawling names")
    arg_parse.add_argument("-i", "--input", type=str, default=None,
                           help="Seed file for crawling. One name per line.")
    arg_parse.add_argument("-o", "--output", type=str, default="fi_names.txt",
                           help="Output file for the names. One name per line.")
    return arg_parse


class User:
    def __init__(self, api_key, user_name=None, password=None):
        self.api_key = api_key
        self.user_name = user_name
        self.password = password


class Connection:
    def __init__(self, user, base_url):
        self.user = user
        self.base_url = base_url
        self.base_time = time.time()

    def get(self, payload):
        payload["api_key"] = self.user.api_key
        payload["format"] = "json"
        if self.base_time + 1 > time.time():
            time.sleep(1)
        self.base_time = time.time()
        r = requests.get(self.base_url, params=payload)
        sys.stderr.write("{}: Retrieved {}\n".format(r.status_code, r.url))
        sys.stderr.flush()
        if r.status_code == 200:
            return json.loads(r.text)
        return None


def get_user_info(conn : Connection, user_name):
    return conn.get({"method": "user.getinfo", "user": user_name})


def get_user_friends(conn : Connection, user_name):
    fp = conn.get({"method": "user.getfriends", "user": user_name})
    if not fp:
        return None
    pc = int(fp["friends"]["@attr"]["totalPages"])
    fl = fp["friends"]["user"]
    if pc < 2:
        return fl
    for i in range(2, pc + 1):
        fp = conn.get({"method": "user.getfriends", "user": user_name, "page": str(i)})
        if fp:
            fl.extend(fp["friends"]["user"])
    return fl


def main(conn, entry_points):
    fil = len(entry_points)
    nfil = 0
    people = 0
    with Tabber("retrieved lists", "finns", "other") as tabb, open("fi_names.txt", 'w') as out_file:
        out_file.write("".join(["{}\n".format(n) for n in entry_points]))
        found = entry_points
        uq = deque()
        uq.extend(entry_points)
        while len(uq) > 0 and fil < 100000:
            un = uq.popleft()
            fl = get_user_friends(conn, un)
            people += 1
            if not fl:
                continue
            for fr in fl:
                if "country" in fr and fr["country"] == "Finland" and "name" in fr and fr["name"] not in found:
                    out_file.write("{}\n".format(fr["name"]))
                    fil += 1
                    uq.append(fr["name"])
                    found.add(fr["name"])
                elif "name" in fr and fr["name"] not in found:
                    found.add(fr["name"])
                    nfil += 1
            tabb(people, fil, nfil)
    print("Found {} people with country == Finland".format(fil))
    print("Found {} people where not country == Finland".format(nfil))


def read_names(seed_file):
    with open(seed_file) as in_file:
        return {e[:-1] for e in in_file.readlines()}


if __name__ == "__main__":
    args = _argparse().parse_args()
    assert args.name or args.input, "either seed file or seed string needs to be supplied"
    seed = [args.name]
    if args.input and isfile(args.input):
        seed = read_names(args.input)
    main(Connection(User(args.api_key), "http://ws.audioscrobbler.com/2.0/"), seed)


