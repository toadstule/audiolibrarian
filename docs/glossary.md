# AudioLibrarian Glossary

This glossary defines the ubiquitous language used throughout the AudioLibrarian
codebase, tests, documentation, and commit messages. These terms represent the
shared domain vocabulary agreed upon by the team.

## Domain Concepts

- **Album** — The conceptual work (e.g., "Dark Side of the Moon"). A Release belongs to an Album.

- **Release** — A specific edition of an Album (e.g., 1973 UK LP, 1992 CD remaster) as
  identified in MusicBrainz. An **immutable metadata description**, built from one of two
  **provenances**: a MusicBrainz response (`Source.MUSICBRAINZ`) or an existing audio file's
  tags (`Source.TAGS`). It references its Album via `album` and `musicbrainz_album_id`.

  *Not an aggregate root, and not a DTO either.* Nothing mutates it, nothing loads or saves
  it by identity, and it owns real behavior (the naming policy it feeds into Library Layout).
  See *Why Release Is Not an Aggregate Root* in `design/adr/0002/ddd-refactoring-plan.md`.

- **Provenance** — Which of the two sources a `Release` was built from. Recorded on
  `Release.source`. Matters because tag-derived releases are single-track projections: they
  describe only the file they came from, not the whole album.

- **Medium** — One physical or digital media unit within a Release (what users
  commonly call "disc" for CDs, "side" for vinyl/cassettes, or just "the album"
  for digital). Has a `media_type` (CD, LP, Cassette, Digital) and `position`
  (e.g., "1 of 2"). The domain model uses "Medium" for precision; UI and
  library paths use format-specific language ("disc", "side", etc.) for
  user-friendliness.

- **Track** — One song on a `Medium`.

- **Library Layout** — The rules mapping release metadata to a location in the library: which
  format tree (`flac`/`m4a`/`mp3`/`source`), the artist directory, the `YYYY__Album`
  directory, whether a `discN` level applies, and the `NN__Title.ext` filename. **These are
  the core domain rules of this project** — the logic most worth centralizing and testing.
  Owned by `domain/services/library_layout.py`.

## Value Objects

- **Performer / People** — credited contributors (value objects).

- **Front Cover** — cover art (value object).

## Infrastructure Concepts

- **Source Audio** — the input to be cataloged: a CD or existing files.

- **Library** — the organized, tagged destination (the `flac`/`m4a`/`mp3`/`source` trees).
  *Repository.* Note it is read as well as written: `rename` and `genre` reconstitute metadata
  from the tags of files already in the tree. The tree plus its tags is the only durable
  representation of a `Release`.

- **Manifest** — a record of what a library entry was made **from**: source type, bitrate,
  MusicBrainz IDs, and disc position, written to `Manifest.yaml` beside the source files. It
  is **provenance only** — not a serialized `Release`, and it does not enable offline
  reconvert. `Reconvert` takes only the disc position from it and re-queries MusicBrainz for
  the metadata. See *Decision: The Manifest Is Provenance Only* in
  `design/adr/0002/ddd-refactoring-plan.md`.

## Use Cases

- **Rip** — Extract audio from a CD and catalog it.

- **Convert** — Transcode existing audio files and catalog them.

- **Reconvert** — Re-transcode from existing source files updating metadata from Musicbrainz.

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
