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
    normalize_gain: 5  # dB gain for normalization
    normalize_preset: "radio"  # "album" or "radio"

    # MusicBrainz API settings (optional)
    musicbrainz:
      username: "your_username"  # For personal genre preferences
      password: "your_password"  # Will be stored securely
      rate_limit: 1.5  # Seconds between API requests
    ```

### 3. Default Values (lowest precedence)

- Built-in defaults from the application

## Available Settings

| Setting                  | Default                   | Description                               |
|--------------------------|---------------------------|-------------------------------------------|
| `library_dir`            | `./library`               | Directory for storing audio files         |
| `work_dir`               | `~/.cache/audiolibrarian` | Directory for temporary files[^wd]        |
| `discid_device`          | `null`                    | CD device path (null for default device)  |
| `normalize_gain`         | `5`                       | Normalization gain in dB                  |
| `normalize_preset`       | `"radio"`                 | Normalization preset ("album" or "radio") |
| `musicbrainz.username`   | (not set)                 | MusicBrainz username[^mb]                 |
| `musicbrainz.password`   | (not set)                 | MusicBrainz password[^mb]                 |
| `musicbrainz.rate_limit` | `1.5`                     | Seconds between requests                  |

[^wd]: The `work_dir` default is actually `$XDG_CACHE_HOME/audiolibrarian`, which defaults
  to `~/.cache/audiolibrarian` on Linux and macOS.

[^mb]: The `musicbrainz` username and password are optional but recommended for accessing personal genre
  preferences on [MusicBrainz](https://musicbrainz.org/).
