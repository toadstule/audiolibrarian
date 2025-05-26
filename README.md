# audiolibrarian #

## Overview ##



## Installation ##

### External Requirements ###

audiolibrarian uses a few command-line tools to run:

* `cdparanoia`: [cd-paranoia](https://xiph.org/paranoia/)
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

Sample `~/.pip/pip.conf`:

```toml
[global]
index-url = "https://pypi.example.com/simple"
```

```bash
pip install --user audiolibrarian
```

### Install from Bitbucket ###

```bash
pip install --user git+https://bitbucket.org/toadstule/audiolibrarian
```

## Configuration ##

The configuration file is `~/.config/audiolibrarian/config.yaml` and can be edited by running 
`audiolibrarian config`.

### Example Configuration ###

```yaml
musicbrainz:
  username: "my_username"
  password: "my_password"
```

### musicbrainz ###

The `musicbrainz` section of the config file contains the username and password for accessing
[MusicBrainz](https://musicbrainz.org/). Having a MusicBrainz account is optional; audiolibrarian 
will use your personal selections for genre if you provide a username and password.

## Usage ##

```bash
audiolibrarian --help
```
