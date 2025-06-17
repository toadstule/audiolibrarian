# audiolibrarian #

## Overview ##

`audiolibrarian` is a command-line tool for ripping audio from CDs (or taking
high-quality audio from local files), tagging them with comprehensive metadata from MusicBrainz,
converting them to multiple formats, and organizing them in a clean directory structure.

### Key Features ###

- **CD Ripping**: Extract audio from CDs with accurate metadata lookup
- **Audio Conversion**: Convert between multiple audio formats (FLAC, M4A, MP3)
- **Metadata Management**: Automatically fetch and apply rich metadata from MusicBrainz
- **File Organization**: Intelligently organize music files into a clean directory structure
- **Batch Processing**: Handle multiple files and directories efficiently
- **Genre Management**: Work with MusicBrainz genres and tags
- **Flexible Configuration**: Customize behavior through config files and environment variables

### Why audiolibrarian? ###

- **Consistent Quality**: Maintains audio quality through the conversion process
- **Accurate Metadata**: Leverages MusicBrainz for comprehensive music information
- **Automated Workflow**: Reduces manual work in organizing and tagging music
- **Open Source**: Free to use and modify under the GPL-3.0 license

Whether you're digitizing a CD collection, organizing existing music files, or managing a large
digital library, `audiolibrarian` provides the tools you need to keep your music collection
well-organized and properly tagged.

## Installation ##

> **NOTE:** This library has only been tested on Linux. It may not work on other operating
> systems.

### External Requirements ###

`audiolibrarian` uses a few command-line tools to run:

- [cd-paranoia](https://www.gnu.org/software/libcdio/)
- [util-linux](https://github.com/util-linux/util-linux)
- [faad2](https://github.com/knik0/faad2)
- [fdkaac](https://github.com/nu774/fdkaac)
- [flac](https://github.com/xiph/flac)
- [lame](https://lame.sourceforge.io/)
- [mpg123](https://www.mpg123.de/)
- [libsndfile](https://github.com/libsndfile/libsndfile)
- [wavegain](https://github.com/MestreLion/wavegain)

It also requires the [libdiscid](https://musicbrainz.org/doc/libdiscid) library.

### Install from PyPI ###

`audiolibrarian` is available on PyPI:

```bash
pip install audiolibrarian
```

## Configuration ##

`audiolibrarian` uses a flexible configuration system that supports multiple configuration sources,
listed in order of precedence:

1. **Environment Variables** (highest precedence)
   - Prefix: `AUDIOLIBRARIAN__`
   - Nested fields: Use `__` as delimiter (e.g., `AUDIOLIBRARIAN__MUSICBRAINZ__USERNAME`)
   - Example:

     ```bash
     # Override library directory (library_dir)
     export AUDIOLIBRARIAN__LIBRARY_DIR="/mnt/music/library"
     
     # Set MusicBrainz credentials (musicbrainz.username and musicbrainz.password)
     export AUDIOLIBRARIAN__MUSICBRAINZ__USERNAME="your_username"
     export AUDIOLIBRARIAN__MUSICBRAINZ__PASSWORD="your_password"
     ```

2. **YAML Configuration File** (medium precedence)
   - Default location: `~/.config/audiolibrarian/config.yaml`
   - Example:

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

3. **Default Values** (lowest precedence)
   - Built-in defaults from the application

### Available Settings ###

| Setting                  | Default                   | Description                               |
|--------------------------|---------------------------|-------------------------------------------|
| `library_dir`            | `./library`               | Directory for storing audio files         |
| `work_dir`               | `~/.cache/audiolibrarian` | Directory for temporary files             |
| `discid_device`          | `null`                    | CD device path (null for default device)  |
| `normalize_gain`         | `5`                       | Normalization gain in dB                  |
| `normalize_preset`       | `"radio"`                 | Normalization preset ("album" or "radio") |
| `musicbrainz.username`   | (not set)                 | MusicBrainz username                      |
| `musicbrainz.password`   | (not set)                 | MusicBrainz password                      |
| `musicbrainz.rate_limit` | `1.5`                     | Seconds between requests                  |

> **Notes**:
>
> - The `musicbrainz` username and password are optional but recommended for accessing personal genre
>   preferences on [MusicBrainz](https://musicbrainz.org/).
> - The `work_dir` default is actually `$XDG_CACHE_HOME/audiolibrarian`, which defaults to
>   `~/.cache/audiolibrarian` on Linux and macOS.

## Usage ##

### Basic Commands ###

```bash
# Rip audio from a CD
audiolibrarian rip

# Convert audio files
audiolibrarian convert /path/to/audio/files

# Create or update manifest files
audiolibrarian manifest /path/to/audio/files

# Reconvert files from existing source
audiolibrarian reconvert /path/to/source/directories

# Rename files based on tags
audiolibrarian rename /path/to/audio/directories

# Manage MusicBrainz genres
audiolibrarian genre /path/to/audio/directories --tag  # Update tags with MB genres

# Show help for all commands
audiolibrarian --help
```

### Directory Structure ###

`audiolibrarian` organizes files in the following structure:

**Processed audio files** (organized by format):

   ```text
   library/
   ├── flac/
   │   └── Artist/
   │       └── YYYY__Album/
   │           ├── 01__Track_Title.flac
   │           └── 02__Another_Track.flac
   ├── m4a/
   │   └── Artist/
   │       └── YYYY__Album/
   │           ├── 01__Track_Title.m4a
   │           └── 02__Another_Track.m4a
   ├── mp3/
   │   └── Artist/
   │   └── YYYY__Album/
   │           ├── 01__Track_Title.mp3
   │           └── 02__Another_Track.mp3
   ├── source/
   │   └── Artist/
   │       └── YYYY__Album/
   │           ├── 01__Track_Title.flac
   │           ├── 02__Another_Track.flac
   │           └── Manifest.yaml
   ```

### Advanced Usage ###

#### Ripping CDs ####

```bash
# Basic CD rip
audiolibrarian rip

# Specify artist and album
audiolibrarian rip --artist "Artist Name" --album "Album Name"

# Specify MusicBrainz release ID (for better metadata)
audiolibrarian rip --mb-release-id "12345678-1234-1234-1234-123456789012"

# Specify disc number for multi-disc sets
audiolibrarian rip --disc "1/2"  # First disc of two
```

#### Converting Audio Files ####

```bash
# Convert with specific artist and album
audiolibrarian convert --artist "Artist Name" --album "Album Name" /path/to/audio/files

# Convert with MusicBrainz release ID
audiolibrarian convert --mb-release-id "12345678-1234-1234-1234-123456789012" /path/to/audio/files

# Convert multi-disc release
audiolibrarian convert --disc "1/2" /path/to/disc1/files
```

#### Working with Manifests ####

```bash
# Create manifest for existing files
audiolibrarian manifest /path/to/audio/files

# Specify CD as source
audiolibrarian manifest --cd /path/to/audio/files

# Specify MusicBrainz artist and release IDs
audiolibrarian manifest \
    --mb-artist-id "12345678-1234-1234-1234-123456789012" \
    --mb-release-id "87654321-4321-4321-4321-210987654321" \
    /path/to/audio/files
```

#### Reconverting Files ####

```bash
# Reconvert all files in directory
audiolibrarian reconvert /path/to/source/directories

# Reconvert with dry run (no changes)
audiolibrarian reconvert --dry-run /path/to/source/directories
```

#### Renaming Files ####

```bash
# Rename files based on tags
audiolibrarian rename /path/to/audio/directories

# Preview renames without making changes
audiolibrarian rename --dry-run /path/to/audio/directories
```

#### Using Different Normalization Presets ####

```bash
# Use radio normalization preset (default)
export AUDIOLIBRARIAN__NORMALIZE_PRESET="radio"

# Use album normalization preset
export AUDIOLIBRARIAN__NORMALIZE_PRESET="album"
```

#### Combining Configuration Sources ####

Configuration sources are combined with the following precedence (highest to lowest):
1. Environment variables
2. YAML configuration file
3. Default values

For example, with this `config.yaml`:

```yaml
# config.yaml
library_dir: /media/music/library
normalize_gain: 5.0
```

And this environment variable:

```bash
export AUDIOLIBRARIAN__NORMALIZE_GAIN="8.0"
```

The effective value of `normalize_gain` will be `8.0` (from the environment variable), while
`library_dir` will be set to `/media/music/library` from the YAML file.

### Troubleshooting ###

#### Increasing Verbosity ####

```bash
# Show more detailed output
audiolibrarian --log-level INFO cd

# Show debug information
audiolibrarian --log-level DEBUG cd
```

#### MusicBrainz Issues ####

If you encounter MusicBrainz-related errors:

1. Verify your credentials are correct
2. Check your Internet connection
3. Use the debug log level to get more information
4. Increase the rate limit if you're hitting rate limits

```bash
export AUDIOLIBRARIAN__MUSICBRAINZ__RATE_LIMIT="2.0"
```
