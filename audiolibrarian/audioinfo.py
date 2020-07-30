import abc
import pprint

from audiolibrarian import text


class AudioInfo(abc.ABC):
    def __init__(self, artist, album, verbose=True):
        self._input_artist = artist
        self._input_album = album
        self._verbose = verbose

        self.artist = ""
        self.artist_sort_name = ""
        self.album = ""
        self.year = ""
        self.genre = ""
        self.front_cover = ""
        self.comments = []
        self.tracks = []

        self._update()
        self._add_filenames()

    def __repr__(self):
        tracks = [f"{t['number'].zfill(2)} - {t['title']} ({t['filename']})" for t in self.tracks]
        return pprint.pformat(
            {
                "artist": self.artist,
                "artist_sort_name": self.artist_sort_name,
                "album": self.album,
                "year": self.year,
                "genre": self.genre,
                "front_cover": len(self.front_cover),
                "tracks": tracks,
                "comments": self.comments,
            },
            width=120,
        )

    def get_comment_string(self):
        return "\n".join(self.comments)

    def get_track(self, number):
        for track in self.tracks:
            if track["number"] == number:
                return track

    def _add_filenames(self):
        tracks = []
        for track in self.tracks:
            track["filename"] = track["number"] + "__" + text.get_filename(track["title"])
            tracks.append(track)
        self.tracks = tracks

    def _pprint(self, name, obj, indent=0):
        if self._verbose:
            print(name, "-" * (78 - len(name)))
            pprint.pp(obj, indent=indent)
            print("-" * 79)

    @abc.abstractmethod
    def _update(self):
        pass
