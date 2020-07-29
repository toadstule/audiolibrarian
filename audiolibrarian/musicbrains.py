import pprint

import musicbrainzngs
from fuzzywuzzy import fuzz

musicbrainzngs.set_useragent("jib-audio", "0.1", "")

# TODO:  release group search sucks for Electronic/Electronic. We may want to do an artist search


class MusicBrainsInfo:
    def __init__(self, artist, album, verbose=True):
        self._input_artist = artist
        self._input_album = album
        self._verbose = verbose

        mb_release_group_list = musicbrainzngs.search_release_groups(
            f"{self._input_artist} {self._input_album}", strict=True
        )["release-group-list"]
        for mb_release_group in mb_release_group_list:
            self._pprint("MB_RELEASE_GROUP", mb_release_group)
            title_l = mb_release_group["title"].lower()
            if not (
                mb_release_group["primary-type"] == "Album"
                and fuzz.ratio(title_l, self._input_album.lower()) > 80
            ):
                continue
            for area in ("US", "XW", "CA", "GB"):  # XW is "Worldwide"
                for fmt in ("CD", "Digital Media"):
                    print(f">>>> looking for {fmt}")
                    for release in mb_release_group["release-list"]:
                        mb_release = musicbrainzngs.get_release_by_id(
                            release["id"], includes=["recordings"]
                        )["release"]
                        self._pprint("- MB_RELEASE", mb_release, indent=2)
                        for mb_release_event in mb_release.get("release-event-list", []):
                            self._pprint("--- EVENT", mb_release_event, indent=4)
                            if area not in mb_release_event.get("area", {}).get(
                                "iso-3166-1-code-list", []
                            ):
                                continue
                            for mb_medium in mb_release["medium-list"]:
                                self._pprint("--- MEDIUM", mb_medium, indent=4)
                                if mb_medium["format"] == fmt:

                                    if mb_release["cover-art-archive"]["front"] == "true":
                                        self.front_cover = musicbrainzngs.get_image_front(
                                            mb_release["id"], size=500
                                        )
                                    else:
                                        self.front_cover = ""
                                    self.medium = mb_medium
                                    self.release = mb_release
                                    self.release_event = mb_release_event
                                    self.release_group = mb_release_group
                                    self.tag_list = mb_release_group.get("tag-list", [])
                                    self.track_list = mb_medium["track-list"]
                                    return
        raise Exception("TODO: handle unable to find stuff in MB")

    def _pprint(self, name, obj, indent=0):
        if self._verbose:
            print(name, "-" * (78 - len(name)))
            pprint.pp(obj, indent=indent)
            print("-" * 79)
