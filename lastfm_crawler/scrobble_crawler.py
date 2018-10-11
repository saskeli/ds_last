from argparse import ArgumentParser
from csv import writer
from os.path import isfile
from tabber import Tabber
from user_crawler import User, Connection


def _argparse():
    arg_parse = ArgumentParser(description="Scrape last.fm for scrobbles made by people in a given file")
    arg_parse.add_argument("api_key", type=str,
                           help="Api key to use for scraping")
    arg_parse.add_argument("-i", "--input", type=str, default="fi_names.txt",
                           help="Path to file containing usernames.")
    arg_parse.add_argument("-o", "--output", type=str, default="scrobbles.txt",
                           help="Path to scrobble file. If file does not exist it will be created.")
    arg_parse.add_argument("-c", "--cache", type=str, default="done_names.txt",
                           help="Path to file containing names of usernames already scraped. If file does not "
                                "exist it will be created.")
    return arg_parse


def read_names(f_path, exclude=None):
    if exclude is None:
        exclude = set()
    with open(f_path) as in_file:
        return {s for s in in_file.read().splitlines() if s not in exclude}


def get_from_json(path, structure, idx=0):
    if structure is None:
        return None
    if idx + 1 >= len(path):
        if type(path[-1]) == str:
            return structure[path[-1]] if path[-1] in structure else None
        if type(path[-1]) == int and len(structure) < path[-1]:
            return structure[path[-1]]
        return None
    if type(path[idx]) == str:
        if path[idx] in structure:
            return get_from_json(path, structure[path[idx]], idx + 1)
        return None
    if type(path[idx]) == int and len(structure) < path[idx]:
        return get_from_json(path, structure[path[idx]], idx + 1)
    return None


def add_scrobbles(tracks, scrobbles, name):
    if not tracks:
        return
    for track in tracks:
        scrobbles.append((name, get_from_json(["url"], track), get_from_json(["artist", "#text"], track),
                          get_from_json(["artist", "mbid"], track), get_from_json(["date", "uts"], track),
                          get_from_json(["mbid"], track)))


def get_user_scrobbles(name, conn):
    scrobbles = []
    js = conn.get({"method": "user.getrecenttracks", "user": name, "limit": 200})
    if not js:
        return None
    pc = int(get_from_json(["recenttracks", "@attr", "totalPages"], js))
    add_scrobbles(get_from_json(["recenttracks", "track"], js), scrobbles, name)
    for i in range(1, pc):
        js = conn.get({"method": "user.getrecenttracks", "user": name, "limit": 200, "page": (i + 1)})
        if not js:
            break
        add_scrobbles(get_from_json(["recenttracks", "track"], js), scrobbles, name)
    return scrobbles


def main(conn, name_list, cache_path, out_path):
    if not isfile(out_path):
        with open(out_path, 'w', newline="") as out_file:
            csv_out = writer(out_file)
            csv_out.writerow(["username", "url", "artist name", "artist id", "uts time", "track id"])
    with Tabber("Users", "Songs", "To go") as tabb, open(cache_path, 'a') as cache_path, \
            open(out_path, 'a', newline="") as out_file:
        csv_out = writer(out_file)
        song_count = 0
        for i, name in enumerate(name_list):
            tabb(i, song_count, len(name_list) - i)
            try:
                scrobbles = get_user_scrobbles(name, conn)
            except (KeyError, ValueError):
                scrobbles = None
            if not scrobbles:
                continue
            song_count += len(scrobbles)
            for scrobble in scrobbles:
                csv_out.writerow(scrobble)
            cache_path.write("{}\n".format(name))
        tabb(len(name_list), song_count, 0)


if __name__ == "__main__":
    args = _argparse().parse_args()
    done_names = set()
    if isfile(args.cache):
        done_names = read_names(args.cache)
    names = read_names(args.input, done_names)
    main(Connection(User(args.api_key), "http://ws.audioscrobbler.com/2.0/"), names, args.cache, args.output)
