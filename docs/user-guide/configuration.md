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

### 2. TOML Configuration File (medium precedence)

- **Default location**: `~/.config/audiolibrarian/config.toml`
- **Example**:

```toml
# AudioLibrarian Configuration
#
# This file was automatically generated. Modify as needed.

# Path to your music library
library_dir = "~/Music/Library"

# Disc ID device (default: system default)
discid_device = "/dev/sr0"

# Working directory for temporary files
work_dir = "~/.cache/audiolibrarian"

[musicbrainz]
# MusicBrainz username and password (optional)
username = "your_username"
password = "your_password"  # Will be stored in plain text!
# Rate limit in seconds between requests
rate_limit = 1.5

[normalize]
# Normalizer to use: "auto", "wavegain", "ffmpeg", or "none"
normalizer = "auto"

[normalize.ffmpeg]
# Target level in dB for ffmpeg normalization
target_level = -13.0

[normalize.wavegain]
# Album gain preset: "album" or "radio"
preset = "radio"
# Gain in dB for wavegain
gain = 5
```

### 3. Default Values (lowest precedence)

- Built-in defaults from the application

## Available Settings

| Setting                         | Default          | Description                               |
|---------------------------------|------------------|-------------------------------------------|
| `library_dir`                   | `./library`      | Directory for storing audio files         |
| `work_dir`                      | (see below)[^wd] | Directory for temporary files             |
| `discid_device`                 | ``               | CD device path (null for default device)  |
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

### Audio Normalization

Audio normalization ensures consistent volume levels across tracks. The following options are available:

- `auto` (default): Automatically selects the best available normalizer (prefers wavegain)
- `wavegain`: Uses the `wavegain` command-line tool (recommended for better album normalization)
- `ffmpeg`: Uses the `ffmpeg-normalize` Python package
- `none`: Skips normalization entirely

#### Wavegain Settings

- `gain`: Adjusts the target volume level (in dB, typically 0-10)
- `preset`: "album" (loudness normalization) or "radio" (peak normalization)

#### FFmpeg Settings

- `target_level`: Target LUFS level (typically between -16 and -12)

## Managing Configuration

The `audiolibrarian config` command helps you manage your configuration:

### Viewing Configuration

To view your current configuration file location and contents:

```bash
audiolibrarian config
```

This will:
1. Show the path to your config file
2. Display the contents of the file if it exists

### Creating a New Configuration

To create a new configuration file with default values:

```bash
audiolibrarian config --init
```

This will:

1. Create a new config file at the default location (`~/.config/audiolibrarian/config.toml`)
2. Populate it with default values
3. Preserve any existing config file (will not overwrite)

### Path Expansion

Configuration paths support the following special expansions:

- `~` is expanded to your home directory

For example:

```toml
library_dir = "~/music/library"  # Expands to /home/username/music/library
```
