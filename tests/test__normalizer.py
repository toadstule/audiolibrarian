"""Tests for the normalizer module."""

#
#  Copyright (c) 2000-2025 Stephen Jibson
#
#  This file is part of audiolibrarian.
#
#  Audiolibrarian is free software: you can redistribute it and/or modify it under the terms of the
#  GNU General Public License as published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  Audiolibrarian is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
#  without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See
#  the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with audiolibrarian.
#  If not, see <https://www.gnu.org/licenses/>.
#
import logging
import pathlib
import shutil
import subprocess

import pytest
import pytest_mock
from _pytest.monkeypatch import MonkeyPatch

from audiolibrarian import config
from audiolibrarian import normalizer as normalizer_


def test_noop_normalizer(tmp_path: pathlib.Path, caplog: pytest.LogCaptureFixture) -> None:
    """Test that NoOpNormalizer does nothing."""
    # Setup logging capture
    caplog.set_level(logging.INFO)

    # Create a test file
    test_file = tmp_path / "test.wav"
    test_file.touch()

    # Initialize and call normalizer
    normalizer = normalizer_.NoOpNormalizer(config.EmptySettings())
    normalizer.normalize({test_file})

    # Verify no changes were made and log message was emitted
    assert test_file.exists()
    log_messages = [record.message for record in caplog.records]
    assert any("Skipping audio normalization" in msg for msg in log_messages)


def test_wavegain_normalizer_success(
    tmp_path: pathlib.Path, mocker: pytest_mock.MockFixture
) -> None:
    """Test WaveGainNormalizer with successful execution."""
    # Setup
    test_file = tmp_path / "test.wav"
    test_file.touch()

    # Mock subprocess.run to simulate successful execution
    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value.returncode = 0
    mock_run.return_value.stderr = b"Normalization complete\n"

    # Execute
    settings = config.NormalizeWavegainSettings(gain=5, preset="radio")
    normalizer = normalizer_.WaveGainNormalizer(settings)
    normalizer.normalize({test_file})

    # Verify command was called correctly
    mock_run.assert_called_once()
    args, kwargs = mock_run.call_args
    assert "wavegain" in args[0][0]
    assert "--radio" in args[0]
    assert "--gain=5" in args[0]
    assert "--apply" in args[0]
    assert str(test_file) in args[0]


def test_ffmpeg_normalizer_success(
    tmp_path: pathlib.Path, mocker: pytest_mock.MockFixture
) -> None:
    """Test FFmpegNormalizer with successful execution."""
    # Setup
    test_file = tmp_path / "test.wav"
    test_file.touch()

    # Mock FFmpegNormalize
    mock_ffmpeg = mocker.patch("ffmpeg_normalize.FFmpegNormalize")

    # Execute
    settings = config.NormalizeFFmpegSettings(target_level=-13.0)
    normalizer = normalizer_.FFmpegNormalizer(settings)
    normalizer.normalize({test_file})

    # Verify FFmpegNormalize was called correctly
    mock_ffmpeg.assert_called_once_with(
        extension="wav",
        keep_loudness_range_target=True,
        target_level=-13.0,
    )
    mock_ffmpeg.return_value.add_media_file.assert_called_once_with(str(test_file), str(test_file))
    mock_ffmpeg.return_value.run_normalization.assert_called_once()


def test_normalizer_factory_none() -> None:
    """Test factory returns NoOpNormalizer when normalizer is 'none'."""
    settings = config.NormalizeSettings(normalizer="none")
    normalizer = normalizer_.Normalizer.factory(settings)
    assert isinstance(normalizer, normalizer_.NoOpNormalizer)


def test_normalizer_factory_wavegain(monkeypatch: MonkeyPatch) -> None:
    """Test factory returns WaveGainNormalizer when wavegain is available."""
    # Mock shutil.which to simulate wavegain being available
    monkeypatch.setattr(
        shutil, "which", lambda x: "/fake/path/wavegain" if x == "wavegain" else None
    )

    settings = config.NormalizeSettings(normalizer="wavegain")
    normalizer = normalizer_.Normalizer.factory(settings)
    assert isinstance(normalizer, normalizer_.WaveGainNormalizer)


def test_normalizer_factory_ffmpeg(monkeypatch: MonkeyPatch) -> None:
    """Test factory returns FFmpegNormalizer when ffmpeg is available."""
    # Mock shutil.which to simulate ffmpeg being available
    monkeypatch.setattr(shutil, "which", lambda x: "/fake/path/ffmpeg" if x == "ffmpeg" else None)

    settings = config.NormalizeSettings(normalizer="ffmpeg")
    normalizer = normalizer_.Normalizer.factory(settings)
    assert isinstance(normalizer, normalizer_.FFmpegNormalizer)


def test_normalizer_factory_auto_wavegain(monkeypatch: MonkeyPatch) -> None:
    """Test factory returns WaveGainNormalizer in auto mode when wavegain is available."""
    # Mock shutil.which to simulate wavegain being available
    monkeypatch.setattr(
        shutil, "which", lambda x: "/fake/path/wavegain" if x == "wavegain" else None
    )

    settings = config.NormalizeSettings(normalizer="auto")
    normalizer = normalizer_.Normalizer.factory(settings)
    assert isinstance(normalizer, normalizer_.WaveGainNormalizer)


def test_normalizer_factory_auto_ffmpeg(monkeypatch: MonkeyPatch) -> None:
    """Test factory returns FFmpegNormalizer in auto mode when ffmpeg is available."""

    # Mock shutil.which to simulate only ffmpeg being available
    def mock_which(cmd: str) -> str | None:
        if cmd == "wavegain":
            return None
        if cmd == "ffmpeg":
            return "/fake/path/ffmpeg"
        return None

    monkeypatch.setattr(shutil, "which", mock_which)

    settings = config.NormalizeSettings(normalizer="auto")
    normalizer = normalizer_.Normalizer.factory(settings)
    assert isinstance(normalizer, normalizer_.FFmpegNormalizer)


def test_normalizer_factory_auto_fallback(monkeypatch: MonkeyPatch) -> None:
    """Test factory falls back to NoOpNormalizer when no normalizers are available."""
    # Mock shutil.which to simulate no normalizers available
    monkeypatch.setattr(shutil, "which", lambda _: None)

    settings = config.NormalizeSettings(normalizer="auto")
    normalizer = normalizer_.Normalizer.factory(settings)
    assert isinstance(normalizer, normalizer_.NoOpNormalizer)


def test_wavegain_normalizer_error_handling(
    tmp_path: pathlib.Path, mocker: pytest_mock.MockFixture, caplog: pytest.LogCaptureFixture
) -> None:
    """Test WaveGainNormalizer error handling."""
    # Setup
    caplog.set_level(logging.INFO)
    test_file = tmp_path / "test.wav"
    test_file.touch()

    # Mock subprocess.run to simulate failure
    mock_run = mocker.patch("subprocess.run")
    mock_result = mocker.Mock()
    mock_result.returncode = 1
    mock_result.stderr = b"Error: File not found\n"
    mock_result.check_returncode.side_effect = subprocess.CalledProcessError(
        returncode=1,
        cmd=["wavegain", "--album", "--gain=7.5", "--apply", str(test_file)],
        stderr=b"Error: File not found\n",
    )
    mock_run.return_value = mock_result

    # Execute & Verify
    settings = config.NormalizeWavegainSettings()
    normalizer = normalizer_.WaveGainNormalizer(settings)
    with pytest.raises(subprocess.CalledProcessError):
        normalizer.normalize({test_file})

    # Verify the error was logged
    assert any("Error:" in record.message for record in caplog.records)
