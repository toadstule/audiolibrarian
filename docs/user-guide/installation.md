# Installation

> **NOTE:** This library has only been tested on Linux. It may not work on other operating
> systems.

## Prerequisites

- Python 3.12 or higher

### External Requirements

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

Instructions for installing these required tools in commonly-used Linux distributions can be
found below.

## Installing with pip

The easiest way to install audiolibrarian is from PyPI:

```bash
pip install audiolibrarian
```

## Verifying the installation

After installation, verify that audiolibrarian is installed correctly:

```bash
audiolibrarian --version
```

You should see the version number printed if the installation was successful.

## Upgrading

To upgrade to the latest version:

```bash
pip install --upgrade audiolibrarian
```

## Uninstalling

To uninstall audiolibrarian:

```bash
pip uninstall audiolibrarian
```

## Installing External Requirements

### Arch Linux

```bash
sudo pacman -S \
    faad2 \
    fdkaac \
    flac \
    lame \
    libcdio-paranoia \
    libdiscid \
    libsndfile \
    mpg123 \
    python-pip \
    util-linux \
    wavegain
```

### Fedora

Fedora Linux is not currently supported because `fdkaac` is not available.

### Ubuntu

```bash
sudo apt update
sudo apt install -y \
    cdparanoia \
    eject \
    faad \
    fdkaac \
    flac \
    lame \
    libdiscid0 \
    libsndfile1 \
    mpg123 \
    python3-pip
```

This will get you everything you need except for `wavegain`. You build and install
`wavegain` from source as follows:

```bash
sudo apt install -y gcc wget unzip
wget "https://www.rarewares.org/files/others/wavegain-1.3.1srcs.zip"
unzip wavegain-1.3.1srcs.zip
cd WaveGain-1.3.1
gcc -fcommon *.c -o wavegain -DHAVE_CONFIG_H -lm
# You'll get some warning here, but they can be ignored.
sudo cp wavegain /usr/loca/bin/wavegain
cd ..
rm -rf WaveGain-1.3.1 wavegain-1.3.1srcs.zip
```
