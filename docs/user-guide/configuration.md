# Configuration

`audiolibrarian` uses a flexible configuration system that supports multiple configuration sources,
listed in order of precedence:

## Configuration Sources

### 1. Environment Variables (highest precedence)

- **Prefix**: `AUDIOLIBRARIAN__`
- **Nested fields**: Use `__` as delimiter (e.g., `AUDIOLIBRARIAN__MUSICBRAINZ__USERNAME`)
- **Example**:

```bash
# Override library directory (library_dir)
export AUDIOLIBRARIAN__LIBRARY_DIR="/mnt/music/library"

# Set MusicBrainz credentials (musicbrainz.username and musicbrainz.password)
export AUDIOLIBRARIAN__MUSICBRAINZ__USERNAME="your_username"
export AUDIOLIBRARIAN__MUSICBRAINZ__PASSWORD="your_password"
```

### 2. YAML Configuration File (medium precedence)

- **Default location**: `~/.config/audiolibrarian/config.yaml`
- **Example**:

```yaml
# Base directory for your music library
library_dir: "~/music/library"

# Cache and working directory
work_dir: "~/.cache/audiolibrarian"

# CD/DVD device path (use null for default device)
discid_device: null

# Audio normalization settings
normalize:
  normalizer: "auto"  # "auto", "wavegain", "ffmpeg", or "none"
  ffmpeg:
    target_level: -13  # Target LUFS level for ffmpeg normalization
  wavegain:
    gain: 5  # dB gain for wavegain normalization (0-10)
    preset: "radio"  # "album" or "radio"

# MusicBrainz API settings (optional)
musicbrainz:
  username: "your_username"  # For personal genre preferences
  password: "your_password"  # Will be stored securely
  rate_limit: 1.5  # Seconds between API requests
```

### 3. Default Values (lowest precedence)

- Built-in defaults from the application

## Available Settings

| Setting                         | Default          | Description                               |
|---------------------------------|------------------|-------------------------------------------|
| `library_dir`                   | `./library`      | Directory for storing audio files         |
| `work_dir`                      | (see below)[^wd] | Directory for temporary files             |
| `discid_device`                 | `null`           | CD device path (null for default device)  |
| `normalize.normalizer`          | `"auto"`         | "auto", "wavegain", "ffmpeg", or "none"   |
| `normalize.ffmpeg.target_level` | `-13`            | Target LUFS level (ffmpeg)                |
| `normalize.wavegain.gain`       | `5`              | Normalization gain in dB (0-10, wavegain) |
| `normalize.wavegain.preset`     | `"radio"`        | "album" or "radio" (wavegain)             |
| `musicbrainz.username`          | (not set)        | MusicBrainz username[^mb]                 |
| `musicbrainz.password`          | (not set)        | MusicBrainz password[^mb]                 |
| `musicbrainz.rate_limit`        | `1.5`            | Seconds between requests                  |

[^wd]: The `work_dir` default is `$XDG_CACHE_HOME/audiolibrarian`, which defaults
  to `~/.cache/audiolibrarian` on Linux and macOS.

[^mb]: The `musicbrainz` username and password are optional but recommended for accessing personal genre
  preferences on [MusicBrainz](https://musicbrainz.org/).

## Audio Normalization

Audio normalization ensures consistent volume levels across tracks. The following options are available:

- `auto` (default): Automatically selects the best available normalizer (prefers wavegain)
- `wavegain`: Uses the `wavegain` command-line tool (recommended for better album normalization)
- `ffmpeg`: Uses the `ffmpeg-normalize` Python package
- `none`: Skips normalization entirely

### Wavegain Settings

- `gain`: Adjusts the target volume level (in dB, typically 0-10)
- `preset`: "album" (loudness normalization) or "radio" (peak normalization)

### FFmpeg Settings

- `target_level`: Target LUFS level (typically between -16 and -12)
