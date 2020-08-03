import abc
import glob
import os
import pprint
import shutil
import subprocess
import tempfile

import discid
import mutagen

from audiolibrarian import cmd
from audiolibrarian.audioinfo import SearchData


class AudioSource(abc.ABC):
    def __init__(self):
        self._temp_dir = tempfile.mkdtemp()

    def __del__(self):
        if os.path.isdir(self._temp_dir):
            shutil.rmtree(self._temp_dir)

    def copy_wavs(self, dest_dir):
        for fn in self.get_wav_filenames():
            shutil.copy2(fn, os.path.join(dest_dir, os.path.basename(fn)))

    @abc.abstractmethod
    def get_search_data(self):
        pass

    @abc.abstractmethod
    def get_source_filenames(self):
        pass

    @abc.abstractmethod
    def get_wav_filenames(self):
        pass

    @abc.abstractmethod
    def prepare_source(self):
        pass


class CDAudioSource(AudioSource):
    def __init__(self):
        self._cd = discid.read(features=["mcn"])
        super().__init__()

    def get_search_data(self):
        return SearchData(disc_id=self._cd.id, disc_mcn=self._cd.mcn)

    def get_source_filenames(self):
        return [
            os.path.join(self._temp_dir, f"track{str(n + 1).zfill(2)}.cdda.wav")
            for n in range(self._cd.last_track_num)
        ]

    def get_wav_filenames(self):
        return self.get_source_filenames()

    def prepare_source(self):
        cwd = os.getcwd()
        os.chdir(self._temp_dir)
        try:
            r = subprocess.run(("cd-paranoia", "-B"))
            r.check_returncode()
        finally:
            os.chdir(cwd)


class FilesAudioSource(AudioSource):
    def __init__(self, filenames):
        super().__init__()
        self._filenames = filenames
        if len(filenames) == 1 and os.path.isdir(filenames[0]):
            # if we're given a directory, figure out what's in there
            for file_type in ("flac", "wav", "m4a", "mp3"):
                fns = sorted(glob.glob(os.path.join(filenames[0], f"*.{file_type}")))
                if fns:
                    self._filenames = fns
                    break

    def get_search_data(self):
        artist, album, mb_artist_id, mb_release_id = "", "", "", ""
        for filename in self._filenames:
            song = mutagen.File(filename)
            pprint.pp(song.tags)
            artist = (
                artist or song.tags.get("ALBUMARTIST", [""])[0] or song.tags.get("ARTIST", [""])[0]
            )
            album = album or song.tags.get("ALBUM", [""])[0]
            mb_artist_id = (
                mb_release_id
                or song.tags.get("MUSICBRAINZ_ALBUMARTISTID", [""])[0]
                or song.tags.get("MUSICBRAINZ_ARTISTID", [""])[0]
            )
            mb_release_id = mb_release_id or song.tags.get("MUSICBRAINZ_ALBUMID", [""])[0]
            print("Artist from tags:", artist)
            print("Album from tags:", album)
            print("MB Artist ID from tags:", mb_artist_id)
            print("MB Release ID from tags:", mb_release_id)
            if mb_artist_id and mb_release_id:
                return SearchData(mb_artist_id=mb_artist_id, mb_release_id=mb_release_id)
            if artist and album:
                return SearchData(artist=artist, album=album)
        return SearchData()

    def get_source_filenames(self):
        return self._filenames

    def get_wav_filenames(self):
        return sorted(glob.glob(os.path.join(self._temp_dir, "*.wav")))

    def prepare_source(self):
        tmp_dir = os.path.join(self._temp_dir, "__tmp__")
        os.makedirs(tmp_dir)
        commands = [
            ("flac", "--silent", "--decode", f"--output-prefix={tmp_dir}/", f)
            for f in self.get_source_filenames()
        ]
        cmd.parallel("Making wav files...", commands, tmp_dir)
        for f in glob.glob(os.path.join(tmp_dir, "*.wav")):
            r = subprocess.run(("sndfile-convert", "-pcm16", f, f.replace("/__tmp__/", "/")))
            r.check_returncode()
        shutil.rmtree(tmp_dir)
