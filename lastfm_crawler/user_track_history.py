import json
import requests
import sys
import time

from argparse import ArgumentParser


def _argparse():
    arg_parse = ArgumentParser(description="Get track history from Last.fm user. Saves it as a json file.")
    arg_parse.add_argument("apikey", type=str,
                           help="last.fm api key to use for crawling.")
    arg_parse.add_argument("username", type=str,
                           help="Username to lookup")
    arg_parse.add_argument("-o", "--output", type=str, default=None,
                           help="Output file for the names. Default: {username}.json")
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


def get_recent_tracks(conn : Connection, user_name):
    page_number = 1
    tracks = [] 
    while True:
        page = conn.get(
            {
                "method": "user.getrecenttracks", 
                "user": user_name,
                "limit": 200,
                "extended": 0,
                "page": page_number
            }
        )
        if not page:
            sys.stderr.write("ERROR: no tracks found, check user name.")
            sys.stderr.flush()
            break
        page_number += 1
        tracks.extend(page['recenttracks']['track'])
        if page_number > int(page['recenttracks']['@attr']['totalPages']):
            break
    return tracks


def main(conn, username, filename):
    tracks = get_recent_tracks(conn, username)
    with open(filename, 'w') as fh:
        fh.write(json.dumps({ 'recenttracks': tracks}))
    print("Wrote {} entries to {}".format(len(tracks), filename))


if __name__ == "__main__":
    args = _argparse().parse_args()
    outfile = args.output or "{}.json".format(args.username)
    main(Connection(User(args.apikey), "http://ws.audioscrobbler.com/2.0/"), args.username, outfile)
