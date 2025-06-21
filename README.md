# audiolibrarian

[![PyPI](https://img.shields.io/pypi/v/audiolibrarian)](https://pypi.org/project/audiolibrarian/)
[![License: GPL-3.0](https://img.shields.io/badge/License-GPL--3.0-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Documentation Status](https://readthedocs.org/projects/audiolibrarian/badge/?version=latest)](https://audiolibrarian.readthedocs.io/)

`audiolibrarian` is a command-line tool for ripping audio from CDs (or taking
high-quality audio from local files), tagging them with comprehensive metadata from MusicBrainz,
converting them to multiple formats, and organizing them in a clean directory structure.

## Features

- **CD Ripping**: Extract audio from CDs with accurate metadata lookup
- **Audio Conversion**: Convert between multiple audio formats (FLAC, M4A, MP3)
- **Metadata Management**: Automatically fetch and apply rich metadata from MusicBrainz
- **File Organization**: Intelligently organize music files into a clean directory structure
- **Batch Processing**: Handle multiple files and directories efficiently

## Basic Usage

```bash
# Rip audio from a CD
audiolibrarian rip

# Convert audio files
audiolibrarian convert /path/to/audio/files

# Get help
audiolibrarian --help
```

## Documentation

For complete documentation, including installation instructions, configuration, and advanced usage, visit:

[https://audiolibrarian.readthedocs.io/](https://audiolibrarian.readthedocs.io/)

## License

This project is licensed under the GPL-3.0 License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please see our [contributing guide](CONTRIBUTING.md) for details.

## Support

For support, please [open an issue](https://github.com/toadstule/audiolibrarian/issues) on GitHub.
