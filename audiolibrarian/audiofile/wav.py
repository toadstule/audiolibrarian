from audiolibrarian.audiofile.audioinfo import ReleaseInfo, TrackInfo
from audiolibrarian.audiofile.audiofile import AudioFile


class WavFile(AudioFile):
    extensions = (".wav",)
