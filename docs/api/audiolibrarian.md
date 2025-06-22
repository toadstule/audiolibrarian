# API Reference

::: audiolibrarian
    options:
      show_root_heading: true
      show_root_full_path: false
      show_root_members_full_path: false
      show_object_full_path: false
      show_category_heading: false
      show_if_no_docstring: true
      separate_signature: true
      merge_init_into_class: true
      heading_level: 2

## Modules

### Core Modules

- `audiolibrarian.cli` - Command-line interface implementation
- `audiolibrarian.config` - Configuration management
- `audiolibrarian.audio` - Audio file handling and processing
- `audiolibrarian.metadata` - Metadata management and MusicBrainz integration
- `audiolibrarian.organize` - File organization and renaming
- `audiolibrarian.utils` - Utility functions and helpers

## Examples

### Basic Usage

```python
from audiolibrarian import AudioLibrarian

# Initialize with custom config
al = AudioLibrarian(config_path="custom_config.yaml")

# Scan a directory
al.scan("/path/to/music")


# Organize files
al.organize("/source/path", "/destination/path")
```

### Working with Metadata

```python
from audiolibrarian.metadata import get_metadata

# Get metadata from MusicBrainz
track_info = get_metadata(artist="Artist Name", title="Track Title")
print(f"Found track: {track_info.title} from {track_info.album}")
```

## Contributing

If you want to contribute to the development of audiolibrarian, please read our [contributing guidelines](../development/contributing.md).
