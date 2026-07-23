# AudioLibrarian Glossary

This glossary defines the ubiquitous language used throughout the AudioLibrarian
codebase, tests, documentation, and commit messages. These terms represent the
shared domain vocabulary agreed upon by the team.

## Domain Concepts

- **Album** — The conceptual work (e.g., "Dark Side of the Moon"). A Release belongs to an Album.

- **Release** — A specific edition of an Album (e.g., 1973 UK LP, 1992 CD remaster)
  as identified in MusicBrainz. *Aggregate root.* Contains references to its Album
  via `album_name` and `album_id`.

- **Medium** — One physical or digital media unit within a Release (what users
  commonly call "disc" for CDs, "side" for vinyl/cassettes, or just "the album"
  for digital). Has a `media_type` (CD, LP, Cassette, Digital) and `position`
  (e.g., "1 of 2"). The domain model uses "Medium" for precision; UI and
  library paths use format-specific language ("disc", "side", etc.) for
  user-friendliness.

- **Track** — One song on a `Medium`.

## Value Objects

- **Performer / People** — credited contributors (value objects).

- **Front Cover** — cover art (value object).

## Infrastructure Concepts

- **Source Audio** — the input to be cataloged: a CD or existing files.

- **Library** — the organized, tagged destination (the `flac`/`m4a`/`mp3`/`source` trees). *Repository.*

- **Manifest** — the persisted provenance of a `Release` in the `Library`, enabling *Reconvert*.

## Use Cases

- **Rip** — Extract audio from a CD and catalog it.

- **Convert** — Transcode existing audio files and catalog them.

- **Reconvert** — Re-transcode from existing source files using stored manifest information.

- **Rename** — Reorganize library files based on tag information.

- **Manifest** — Write or update manifest files for provenance tracking.

- **Genre** — Manage genre metadata in MusicBrainz and audio files.

## Ports & Adapters

- **Metadata Provider** — the source of truth for identification (MusicBrainz).

- **Encoder** — transcoding service (FLAC, M4A, MP3).

- **Normalizer** — loudness normalization service (ffmpeg, wavegain).

- **Tag Gateway** — read/write metadata from audio files (FLAC, M4A, MP3 taggers).

- **User Interface** — prompts, confirmations, and summaries (ConsoleUI).

## Architecture Layers

- **Domain Layer** — Pure business logic with no infrastructure concerns
  (entities, value objects, domain services).

- **Application Layer** — Orchestrates domain objects to fulfill use cases; defines ports (interfaces).

- **Infrastructure Layer** — Implements port interfaces as adapters; handles
  external concerns (MusicBrainz, filesystem, encoders).

- **Presentation Layer** — CLI-specific code and composition root; wires adapters into use cases.
