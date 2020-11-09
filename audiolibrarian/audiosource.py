import abc
import os
import shutil
import subprocess
import tempfile
from logging import getLogger
from pathlib import Path
from typing import Dict, List

import discid

from audiolibrarian import cmd
from audiolibrarian.audiofile import open_
from audiolibrarian.text import alpha_numeric_key

log = getLogger(__name__)


class AudioSource(abc.ABC):
    def __init__(self):
        self._temp_dir = Path(tempfile.mkdtemp())

    def __del__(self):
        if self._temp_dir.is_dir():
            shutil.rmtree(self._temp_dir)

    def copy_wavs(self, dest_dir) -> None:
        for fn in self.get_wav_filenames():
            shutil.copy2(fn, dest_dir / fn.name)

    @abc.abstractmethod
    def get_search_data(self) -> Dict[str, str]:
        pass

    @abc.abstractmethod
    def get_source_filenames(self) -> List[Path]:
        pass

    @abc.abstractmethod
    def get_wav_filenames(self) -> List[Path]:
        pass

    @abc.abstractmethod
    def prepare_source(self) -> None:
        pass


class CDAudioSource(AudioSource):
    def __init__(self):
        super().__init__()
        self._cd = discid.read(features=["mcn"])

    def get_search_data(self) -> Dict[str, str]:
        return {"disc_id": self._cd.id, "disc_mcn": self._cd.mcn}

    def get_source_filenames(self) -> List[Path]:
        return [
            self._temp_dir / f"track{str(n + 1).zfill(2)}.cdda.wav"
            for n in range(self._cd.last_track_num)
        ]

    def get_wav_filenames(self) -> List[Path]:
        return self.get_source_filenames()

    def prepare_source(self) -> None:
        cwd = Path.cwd()
        os.chdir(self._temp_dir)
        try:
            r = subprocess.run(("cd-paranoia", "-B"))
            r.check_returncode()
        finally:
            os.chdir(cwd)
        subprocess.run(("eject",))


class FilesAudioSource(AudioSource):
    def __init__(self, filenames: List[Path]):
        super().__init__()
        self._filenames = filenames
        if len(filenames) == 1 and filenames[0].is_dir():
            # if we're given a directory, figure out what's in there
            for file_type in ("flac", "wav", "m4a", "mp3"):
                if fns := sorted(filenames[0].glob(f"*.{file_type}"), key=alpha_numeric_key):
                    self._filenames = list(fns)
                    break
        self._file_type = self._filenames[0].suffix.lstrip(".")

    def get_search_data(self) -> Dict[str, str]:
        for filename in self._filenames:
            one_track = open_(filename).one_track
            release = one_track.release
            track = one_track.track

            artist = release.first("artists") or track.artist or track.first("artists") or ""
            album = release.album or ""
            mb_artist_id = (
                release.first("musicbrainz_album_artist_ids")
                or track.first("musicbrainz_artist_ids")
                or ""
            )
            mb_release_id = release.musicbrainz_album_id or ""
            log.info(f"Artist from tags: {artist}")
            log.info(f"Album from tags: {album}")
            log.info(f"MB Artist ID from tags: {mb_artist_id}")
            log.info(f"MB Release ID from tags: {mb_release_id}")
            if mb_artist_id and mb_release_id:
                return {"mb_artist_id": mb_artist_id, "mb_release_id": mb_release_id}
            if artist and album:
                return {"artist": artist, "album": album}
        return {}

    def get_source_filenames(self) -> List[Path]:
        return self._filenames

    def get_wav_filenames(self) -> List[Path]:
        return sorted(self._temp_dir.glob("*.wav"), key=alpha_numeric_key)

    def prepare_source(self) -> None:
        tmp_dir = self._temp_dir / "__tmp__"
        tmp_dir.mkdir(parents=True)
        if self._file_type == "flac":
            commands = [
                ("flac", "--silent", "--decode", f"--output-prefix={tmp_dir}/", f)
                for f in self.get_source_filenames()
            ]
        elif self._file_type == "m4a":
            commands = [
                ("faad", "-q", "-o", f"{tmp_dir}/{f.name.replace('.m4a', '.wav')}", f)
                for f in self.get_source_filenames()
            ]
        elif self._file_type == "mp3":
            commands = [
                (
                    "mpg123",
                    "-q",
                    "-w",
                    f"{tmp_dir}/{f.name.replace('.mp3', '.wav')}",
                    f,
                )
                for f in self.get_source_filenames()
            ]
        else:
            raise Exception(f"Unsupported source file type: {self._file_type}")
        cmd.parallel(f"Making {len(commands)} wav files...", commands)
        cmd.touch(tmp_dir.glob("*.wav"))
        for f in tmp_dir.glob("*.wav"):
            r = subprocess.run(("sndfile-convert", "-pcm16", f, str(f).replace("/__tmp__/", "/")))
            r.check_returncode()
        shutil.rmtree(tmp_dir)
