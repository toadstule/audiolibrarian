#  Copyright (C) 2020-2025 Stephen T. Jibson.
#  SPDX-License-Identifier: GPL-3.0-only

"""Tests for the normalizer module."""

import logging
import pathlib
import subprocess

import pytest
import pytest_mock
from _pytest.monkeypatch import MonkeyPatch

from audiolibrarian import config
from audiolibrarian.infrastructure.normalizers.ffmpeg import FFmpegNormalizer
from audiolibrarian.infrastructure.normalizers.noop import NoOpNormalizer
from audiolibrarian.infrastructure.normalizers.normalizer import Normalizer
from audiolibrarian.infrastructure.normalizers.wavegain import WaveGainNormalizer


def test_noop_normalizer(tmp_path: pathlib.Path, caplog: pytest.LogCaptureFixture) -> None:
    """Test that NoOpNormalizer does nothing."""
    # Setup logging capture
    caplog.set_level(logging.INFO)

    # Create a test file
    test_file = tmp_path / "test.wav"
    test_file.touch()

    # Initialize and call normalizer
    normalizer = NoOpNormalizer(config.EmptySettings())
    normalizer.normalize({test_file})

    # Verify no changes were made and log message was emitted
    assert test_file.exists()
    log_messages = [record.message for record in caplog.records]
    assert any("Skipping audio normalization" in msg for msg in log_messages)


def test_wavegain_normalizer_success(tmp_path: pathlib.Path, mocker: pytest_mock.MockFixture) -> None:
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
    normalizer = WaveGainNormalizer(settings)
    normalizer.normalize({test_file})

    # Verify command was called correctly
    mock_run.assert_called_once()
    args, kwargs = mock_run.call_args
    assert "wavegain" in args[0][0]
    assert "--radio" in args[0]
    assert "--gain=5" in args[0]
    assert "--apply" in args[0]
    assert str(test_file) in args[0]


def test_ffmpeg_normalizer_success(tmp_path: pathlib.Path, mocker: pytest_mock.MockFixture) -> None:
    """Test FFmpegNormalizer with successful execution."""
    # Setup
    test_file = tmp_path / "test.wav"
    test_file.touch()

    # Mock FFmpegNormalize
    mock_ffmpeg = mocker.patch("ffmpeg_normalize.FFmpegNormalize")

    # Execute
    settings = config.NormalizeFFmpegSettings(target_level=-13.0)
    normalizer = FFmpegNormalizer(settings)
    normalizer.normalize({test_file})

    # Verify FFmpegNormalize was called correctly
    mock_ffmpeg.assert_called_once_with(
        audio_codec="pcm_s16le",
        extension="wav",
        extra_output_options=["-ar:a", "44100"],
        keep_loudness_range_target=True,
        target_level=-13.0,
    )
    mock_ffmpeg.return_value.add_media_file.assert_called_once_with(str(test_file), str(test_file))
    mock_ffmpeg.return_value.run_normalization.assert_called_once()


def test_normalizer_factory_none() -> None:
    """Test factory returns NoOpNormalizer when normalizer is 'none'."""
    settings = config.NormalizeSettings(normalizer="none")
    normalizer = Normalizer.factory(settings)
    assert isinstance(normalizer, NoOpNormalizer)


def test_normalizer_factory_wavegain(monkeypatch: MonkeyPatch) -> None:
    """Test factory returns WaveGainNormalizer when wavegain is available."""
    # Ensure wavegain is in registry
    original_registry = Normalizer._registry.copy()
    Normalizer._registry["wavegain"] = WaveGainNormalizer

    try:
        settings = config.NormalizeSettings(normalizer="wavegain")
        normalizer = Normalizer.factory(settings)
        assert isinstance(normalizer, WaveGainNormalizer)
    finally:
        Normalizer._registry = original_registry


def test_normalizer_factory_ffmpeg(monkeypatch: MonkeyPatch) -> None:
    """Test factory returns FFmpegNormalizer when ffmpeg is available."""
    # Ensure ffmpeg is in registry
    original_registry = Normalizer._registry.copy()
    Normalizer._registry["ffmpeg"] = FFmpegNormalizer

    try:
        settings = config.NormalizeSettings(normalizer="ffmpeg")
        normalizer = Normalizer.factory(settings)
        assert isinstance(normalizer, FFmpegNormalizer)
    finally:
        Normalizer._registry = original_registry


def test_normalizer_factory_auto_wavegain(monkeypatch: MonkeyPatch) -> None:
    """Test factory returns WaveGainNormalizer in auto mode when wavegain is available."""
    # Ensure both are in registry and wavegain is auto-selected
    original_registry = Normalizer._registry.copy()
    original_auto_normalizer = Normalizer._auto_normalizer
    original_auto_priority = Normalizer._auto_priority
    Normalizer._registry["wavegain"] = WaveGainNormalizer
    Normalizer._registry["ffmpeg"] = FFmpegNormalizer
    Normalizer._auto_normalizer = WaveGainNormalizer
    Normalizer._auto_priority = 2  # WaveGain priority

    try:
        settings = config.NormalizeSettings(normalizer="auto")
        normalizer = Normalizer.factory(settings)
        assert isinstance(normalizer, WaveGainNormalizer)
    finally:
        Normalizer._registry = original_registry
        Normalizer._auto_normalizer = original_auto_normalizer
        Normalizer._auto_priority = original_auto_priority


def test_normalizer_factory_auto_ffmpeg(monkeypatch: MonkeyPatch) -> None:
    """Test factory returns FFmpegNormalizer in auto mode when ffmpeg is available."""
    # Ensure only ffmpeg is in registry
    original_registry = Normalizer._registry.copy()
    original_auto_normalizer = Normalizer._auto_normalizer
    original_auto_priority = Normalizer._auto_priority
    Normalizer._registry.pop("wavegain", None)
    Normalizer._registry["ffmpeg"] = FFmpegNormalizer
    Normalizer._auto_normalizer = FFmpegNormalizer
    Normalizer._auto_priority = 1  # FFmpeg priority

    try:
        settings = config.NormalizeSettings(normalizer="auto")
        normalizer = Normalizer.factory(settings)
        assert isinstance(normalizer, FFmpegNormalizer)
    finally:
        Normalizer._registry = original_registry
        Normalizer._auto_normalizer = original_auto_normalizer
        Normalizer._auto_priority = original_auto_priority


def test_normalizer_factory_auto_fallback(monkeypatch: MonkeyPatch) -> None:
    """Test factory falls back to NoOpNormalizer when no normalizers are available."""
    # Ensure no normalizers are in registry
    original_registry = Normalizer._registry.copy()
    original_auto_normalizer = Normalizer._auto_normalizer
    original_auto_priority = Normalizer._auto_priority
    Normalizer._registry.pop("wavegain", None)
    Normalizer._registry.pop("ffmpeg", None)
    Normalizer._auto_normalizer = None
    Normalizer._auto_priority = -1

    try:
        settings = config.NormalizeSettings(normalizer="auto")
        normalizer = Normalizer.factory(settings)
        assert isinstance(normalizer, NoOpNormalizer)
    finally:
        Normalizer._registry = original_registry
        Normalizer._auto_normalizer = original_auto_normalizer
        Normalizer._auto_priority = original_auto_priority


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
    normalizer = WaveGainNormalizer(settings)
    with pytest.raises(subprocess.CalledProcessError):
        normalizer.normalize({test_file})

    # Verify the error was logged
    assert any("Error:" in record.message for record in caplog.records)
