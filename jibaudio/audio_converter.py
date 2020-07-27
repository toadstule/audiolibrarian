"""audio_converter

"""
import os


class UnsupportedDestinationFileType(Exception):
    """Unsupported Destination File Type."""


class UnsupportedSourceFileType(Exception):
    """Unsupported Source File Type."""


class AudioConverter(object):
    """Audio Converter.

    Contains methods to convert audio files.
    """

    SOURCE_TYPES = ("FLAC", "WAV")

    def __init__(self, source_file_name, source_file_type):
        """Constructor.

        :param source_file_name: The file name of the source file.

        :param source_file_type: The type of the source file ('FLAC', 'WAV').
        """
        self._source_file_name = source_file_name
        self._source_file_type = source_file_type

        if self._source_file_type not in self.SOURCE_TYPES:
            raise UnsupportedSourceFileType(self._source_file_type)

    def to_flac(self, silent=False):
        """Convert to FLAC."""
        destination_file_name = self._get_destination_file_name(
            destination_file_type="FLAC"
        )
        if self._source_file_type == "AVI":
            command = (
                f'ffmpeg -i "{self._source_file_name}" -c:v libx264 -crf 19 -preset slow -c:a aac -strict '
                f'experimental -b:a 192k -ac 2 "{destination_file_name}"'
            )
        elif self._source_file_type == "HEVC":
            command = f'ffmpeg -i "{self._source_file_name}" -c:a copy -x265-params crf=25 "{destination_file_name}"'
        else:
            raise UnsupportedSourceFileType(self._source_file_type)

        if silent:
            command += " >& /dev/null"
        os.system(command)

    def _get_destination_file_name(self, destination_file_type):
        # get destination file name based on source file name
        if destination_file_type == "AVC":
            if self._source_file_type == "AVI":
                result = self._source_file_name.replace("avi", "mp4")
            elif self._source_file_type == "HEVC":
                result = self._source_file_name.replace("hevc", "avc").replace(
                    "HEVC", "AVC"
                )
                result = result.replace("265", "264").replace(".mkv", ".mp4")
            else:
                raise UnsupportedSourceFileType(self._source_file_type)
            if result == self._source_file_name:
                result += ".mp4"
        else:
            raise UnsupportedDestinationFileType(destination_file_type)

        return result
