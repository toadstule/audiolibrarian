# audiolibrarian #

## Overview ##



## Installation ##

### External Requirements ###

audiolibrarian uses a few command-line tools to run:

* `cd-paranoia`: [cd-paranoia](https://www.gnu.org/software/libcdio/)
* `eject`: [util-linux](https://github.com/util-linux/util-linux)
* `faad`: [faad2](https://github.com/knik0/faad2)
* `fdkaac`: [fdkaac](https://github.com/nu774/fdkaac)
* `flac`: [flac](https://github.com/xiph/flac)
* `lame`: [lame](https://lame.sourceforge.io/)
* `mpg123`: [mpg123](https://www.mpg123.de/)
* `sndfile-convert`: [libsndfile](https://github.com/libsndfile/libsndfile)
* `wavegain`: [wavegain](https://rarewares.org/others.php) 

### Install from PyPI ###

audiolibrarian is not available on PyPI, but it can be installed from a local PyPI.

```bash
pip install --user --extra_index_url=https://pypi.example.com/simple audiolibrarian
```

### Install from Bitbucket ###

```bash
pip install --user git+https://bitbucket.org/toadstule/audiolibrarian
```

## Configuration ##

AudioLibrarian uses a flexible configuration system that supports multiple configuration sources:

1. Environment Variables (highest precedence)
   - Prefix: "AUDIOLIBRARIAN__"
   - Nested fields: Use "__" as delimiter (e.g., AUDIOLIBRARIAN__MUSICBRAINZ__USERNAME)

2. YAML Configuration File
   - Location: `$XDG_CONFIG_HOME/audiolibrarian/config.yaml` (default: `~/.config/audiolibrarian/config.yaml`)
   - Supports nested structure for MusicBrainz settings

3. Default Values (lowest precedence)
   - Defined in the project source

### Available Settings ###

| Setting                  | Default                          | Description                               |
|--------------------------|----------------------------------|-------------------------------------------|
| `library_dir`            | `library` (in the current dir)   | Directory for storing audio files         |
| `work_dir`               | `$XDG_CACHE_HOME/audiolibrarian` | Directory for temporary files             |
| `discid_device`          | `null`                           | CD device path (null for default device)  |
| `normalize_gain`         | `5`                              | Normalization gain in dB                  |
| `normalize_preset`       | `"radio"`                        | Normalization preset ("album" or "radio") |
| `musicbrainz.username`   | `""`                             | MusicBrainz username                      |
| `musicbrainz.password`   | `""`                             | MusicBrainz password                      |
| `musicbrainz.rate_limit` | `1.5`                            | Seconds between requests                  |

### Environment Variables ###

You can override any setting using environment variables with the "AUDIOLIBRARIAN__" prefix. For example:

```bash
# Override library directory
export AUDIOLIBRARIAN__LIBRARY_DIR="/path/to/music_library"

# Override MusicBrainz settings
export AUDIOLIBRARIAN__MUSICBRAINZ__USERNAME="my_username"
export AUDIOLIBRARIAN__MUSICBRAINZ__PASSWORD="my_password"
```

### MusicBrainz Settings ###

The `musicbrainz` section contains settings for accessing [MusicBrainz](https://musicbrainz.org/). Having a MusicBrainz account is optional, but providing credentials allows audiolibrarian to use your personal selections for genre.

## Usage ##

```bash
audiolibrarian --help
```
