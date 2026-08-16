# DDD Refactoring Plan (Integrated Approach)

This document outlines the step-by-step plan for refactoring audiolibrarian to adopt
Domain-Driven Design principles using a pragmatic hexagonal architecture, as described
in ADR 0002. It serves as a working document for planning and tracking the migration
effort.

> **Revised during Phase 1.1.** Implementing "Release as an aggregate root" surfaced that
> `Release` is not one — nothing mutates it, nothing loads or saves it by identity, and its
> only invariant lives on a value object. Phase 1.1 was rewritten to *freeze* the metadata
> model instead of encapsulating it, and a new Phase 1.2 promotes **Library Layout** to the
> centre of the domain, since that is where the real business rules (and a live bug) turned
> out to be. See *Why Release Is Not an Aggregate Root* and *Decision: The Manifest Is
> Provenance Only*. A more radical alternative was considered and rejected —
> see `alternate-ddd-refactoring-plan.md`.

## Overview

The refactoring will be executed incrementally in phases to minimize disruption and allow
for continuous testing. Each phase builds on the previous one, with the goal of achieving a
clean separation between presentation, application, domain, and infrastructure layers.

**Key Approach Decisions**:

- **Learning-oriented**: Each phase includes "why" explanations to teach DDD concepts
- **Aggressive cleanup**: Old files will be deleted promptly after each phase; git preserves
  history if needed
- **No backward compatibility concerns**: Small current user base allows breaking changes
- **Test-green phases**: Each phase keeps the test suite green; strangler pattern approach
- **Architecture enforcement**: Import-linter contract makes dependency rule executable
- **Rollback strategy**: Each phase is a separate commit; if a phase gets stuck, use
  `git reset --hard HEAD~1` to rollback

## Target Architecture

### Domain Layer

Contains pure business logic with no external dependencies.

```text
src/audiolibrarian/domain/
├── __init__.py
├── model/
│   ├── __init__.py
│   ├── release.py        # Release, Medium, Track    [immutable metadata description]
│   │                     # NOT an aggregate root - see "Why Release Is Not an
│   │                     # Aggregate Root" below. Built from one of two provenances:
│   │                     # a MusicBrainz response, or an audio file's tags.
│   │                     # Release references its Album via album / musicbrainz_album_id
│   ├── values.py         # FrontCover, FileInfo, Performer, People,
│   │                     # MediumPosition, TrackNumber, AudioFormat    [value objects]
│   └── enums.py          # BitrateMode, FileFormat, Source
└── services/
    ├── __init__.py
    ├── source_matching.py  # match source files → tracks; count invariant
    └── library_layout.py   # THE core domain rules: format trees, artist/album dir,
                            # the discN rule, track filenames. Single source of truth.
```

**Where the domain logic actually is.** The centre of gravity is
`services/library_layout.py`, not `model/release.py`. `Release` is an immutable description
that carries metadata *into* the layout rules; the rules themselves — which tree, which
directory, whether a `discN` level applies, what the file is called — are the business logic
worth protecting. Phase 1.2 makes that explicit.

### Application Layer

Orchestrates domain objects to fulfill use cases. Defines ports (interfaces) that the
core needs.

```text
src/audiolibrarian/application/
├── __init__.py
├── ports/              # interfaces the core needs (abstractions it OWNS)
│   ├── __init__.py
│   ├── metadata_provider.py
│   ├── audio_source.py
│   ├── tag_gateway.py       # read/write tags (today's TagGateway ABC)
│   ├── encoder.py
│   ├── normalizer.py
│   ├── library_repository.py
│   └── user_interface.py    # prompts, confirmations, summaries
└── use_cases/          # application services (thin orchestration)
    ├── __init__.py
    ├── rip_album.py
    ├── convert_files.py
    ├── reconvert_library.py
    ├── rename_library.py
    ├── write_manifest.py
    └── manage_genre.py
```

### Infrastructure Layer

Implements port interfaces as adapters. Handles external concerns.

```text
src/audiolibrarian/infrastructure/
├── __init__.py
├── musicbrainz/        # ACL: implements MetadataProvider
│   ├── __init__.py
│   ├── musicbrainz_provider.py
│   └── musicbrainz_mapper.py
├── audiosources/       # CD + Files adapters
│   ├── __init__.py
│   ├── cd_source.py
│   └── file_source.py
├── tags/               # FLAC/M4A/MP3 tag adapters
│   ├── __init__.py
│   ├── flac_tagger.py
│   ├── m4a_tagger.py
│   └── mp3_tagger.py
├── encoders/           # flac/m4a/mp3 encoder adapters (from Base._make_*)
│   ├── __init__.py
│   ├── flac_encoder.py
│   ├── m4a_encoder.py
│   └── mp3_encoder.py
├── normalizers/        # ffmpeg/wavegain adapters
│   ├── __init__.py
│   ├── ffmpeg_normalizer.py
│   └── wavegain_normalizer.py
├── library/            # FilesystemLibraryRepository + manifest persistence
│   ├── __init__.py
│   └── filesystem_library_repository.py
└── shell.py            # today's sh.py
```

**Note**: Each adapter module's `__init__.py` will contain factory functions for creating
adapter instances (e.g., `encoders/__init__.py` exports `create_encoders()` that returns all
three encoder instances).

### Presentation Layer

CLI-specific code and composition root.

```text
src/audiolibrarian/presentation/
├── __init__.py
├── cli/                # argparse + thin command adapters + composition root
│   ├── __init__.py
│   ├── command_handlers.py
│   └── composition_root.py
└── console_ui.py       # implements UserInterface (print/input/summary table)
```

## Testing Strategy

### Principles

- **Test-first for new domain logic**: Write tests before implementing new domain services
  and value objects
- **Maintain existing test coverage**: All existing tests must pass after each phase
- **Test at appropriate levels**: Unit tests for domain logic, integration tests for
  infrastructure, end-to-end tests for workflows
- **Use test doubles**: Mock external dependencies (MusicBrainz API, file system) in
  domain layer tests
- **Use pytest-vcr for external API tests**: Record/replay real API responses for
  MusicBrainz integration tests to avoid rate limiting and network flakiness

### Test Organization

```text
tests/
├── unit/
│   ├── domain/
│   │   ├── model/
│   │   │   ├── test_release.py
│   │   │   ├── test_medium.py
│   │   │   ├── test_track.py
│   │   │   └── test_values.py
│   │   └── services/
│   │       ├── test_source_matching.py
│   │       └── test_library_layout.py
│   └── application/
│       ├── test_rip_album.py
│       ├── test_convert_files.py
│       └── test_reconvert_library.py
├── integration/
│   ├── infrastructure/
│   │   ├── test_musicbrainz_provider.py
│   │   ├── test_filesystem_library_repository.py
│   │   ├── test_encoders.py
│   │   └── test_taggers.py
│   └── test_end_to_end.py
└── fixtures/
    └── test_data/
```

### Per-Phase Testing Requirements

#### Phase 0: Language & Guardrails

- Run full test suite after creating skeleton
- No new tests required (pure structural change)
- Verify import-linter contract passes
- Update imports in existing tests to reference new locations if needed

#### Phase 1: Purify Domain Model

- Write unit tests for each new value object before implementation
- Test invariants (e.g., MediumPosition validation, TrackNumber formatting)
- Ensure existing tests still pass after moving entities
- Test that value objects are immutable (frozen dataclass)

#### Phase 1.1: Freeze the Metadata Model

- Assert `Release`, `Medium`, `Track`, and `OneTrack` all raise
  `attrs.exceptions.FrozenInstanceError` on attribute assignment
- Cover the two `attrs.evolve` sites: front-cover backfill produces a *new* `Release` and
  leaves the original untouched; `Source.TAGS` stamping survives the
  `Release(...) or None` truthiness check
- Revert the private-attribute reach-arounds in `tests/test__musicbrainz.py`
- `mypy src/` must be clean — frozen classes surface any missed assignment site
- No new tests for aggregate invariants: there are none to test

#### Phase 1.2: Library Layout

- Test-first, since this is new domain logic:
  - `library_layout` yields identical `discN` decisions for a CLI-derived and a tag-derived
    medium position (the divergence this phase removes)
  - single-medium releases get **no** `discN` component; multi-medium releases get one
  - format tree names come from one place
  - track filenames round-trip through `TrackNumber.from_filename`
- **Regression test for the manifest path bug**: a two-medium release must write two distinct
  `Manifest.yaml` files, under `source/Artist/YYYY__Album/disc1/` and `.../disc2/`
- End-to-end check that the write path and read path now agree — see Success Criteria

#### Phase 2: Declare Ports

- Write unit tests for port interfaces using test doubles
- Ensure existing tests still pass after moving ABCs
- Add integration tests for accidental ports (AudioSource, Normalizer, TagGateway)
- Test that adapters correctly implement port interfaces

#### Phase 3: Extract Infrastructure

- Write unit tests for repository interfaces using test doubles
- Write integration tests for filesystem repository implementations
- Write integration tests for MusicBrainz ACL using pytest-vcr to record/replay API
  responses
- Test encoder adapters with real subprocess calls in integration suite
- Test that infrastructure has no dependencies on application/presentation

#### Phase 4: Extract Presentation

- Write unit tests for UserInterface port using test doubles
- Write integration tests for ConsoleUI adapter
- Ensure all I/O is behind the port (no print/input in core)
- Test that prompts and summaries render correctly

#### Phase 5: Use Cases

- Write unit tests for application services
- Write integration tests for command handlers
- Ensure CLI commands work as before (regression testing)
- Test that orchestration logic is correctly delegated to application services
- Test composition root wiring

#### Phase 6: Retire Base

- Split tests into domain/use-case/adapter categories
- Ensure domain tests have no mocks (pure objects)
- Ensure use-case tests use fake adapters
- Ensure adapter tests are integration tests
- Run full regression test suite
- Verify all import-linter contracts still pass

### Continuous Testing

- Run `pytest` after each significant change within a phase
- Use `pytest-xdist` for parallel test execution to speed up feedback
- Set up pre-commit hooks to run relevant tests
- Consider adding a CI gate that requires all tests to pass before merging

### Test Data Management

- Keep existing test data in `tests/test_data/`
- Add fixtures for new domain objects as needed
- Use direct instantiation with attrs classes for test data (e.g.,
  `Release(album="Dark Side", ...)`)
- Add factory_boy later if test setup becomes repetitive
- Ensure test data is isolated and doesn't leak between tests

### Coverage Goals

- Maintain current coverage levels throughout migration
- Target 80%+ coverage for new domain layer code
- Focus coverage on business-critical paths
- Use `pytest-cov` to generate coverage reports

## Migration Phases

### Phase 0: Language & Guardrails *(no behavior change)*

**Tasks**:

- Write the ubiquitous language glossary into `docs/glossary.md`
- Create the empty `domain/ application/ infrastructure/ presentation/` skeleton with
  `__init__.py` files
- Add import-linter contract enforcing the dependency rule:
  - Install `import-linter` package
  - Configure import-linter in pyproject.toml:

    ```toml
    [tool.importlinter]
    root_package = "audiolibrarian"

    [[tool.importlinter.contracts]]
    name = "domain-layer-dependency-rule"
    type = "layers"
    layers = [
        "audiolibrarian.presentation",
        "audiolibrarian.infrastructure",
        "audiolibrarian.application",
        "audiolibrarian.domain",
    ]
    container = "audiolibrarian"
    ```

  - This ensures: domain imports nothing, application imports only domain,
    infrastructure imports only application+domain, presentation imports only
    application+domain+infrastructure
- Add pre-commit hook or CI check for import-linter
- Add pytest-vcr to dev dependencies in pyproject.toml for MusicBrainz API testing
- Run full test suite to ensure skeleton doesn't break anything

**Why first**: The language and the dependency rule are the two things that, once agreed,
make every later decision obvious. The linter makes the architecture executable - violations
fail CI instead of rotting silently.

**DDD concept taught**: Ubiquitous Language, the Dependency Rule

**Learning checkpoint**: Why is the dependency rule important? What happens if it's
violated?

---

### Phase 1: Purify the Domain Model

**Tasks**:

- Move `records.py` into `domain/model/` split into:
  - `release.py` - Release, Medium, Track (Release references its Album via `album` and
    `musicbrainz_album_id`)
  - `values.py` - FrontCover, FileInfo, Performer, People value objects
  - `enums.py` - BitrateMode, FileFormat, Source enums
- Freeze value objects with `@attrs.define(frozen=True)` (attrs is already a project
  dependency)
- Introduce new value objects to cure primitive obsession:
  - `MediumPosition(number, count)` - validates `1 ≤ number ≤ count` once
  - `TrackNumber(int)` - knows how to render as `"02"` and parse from filename
  - `AudioFormat` - FLAC/M4A/MP3 as first-class concept
- Keep existing behavior methods (`get_filename`, path helpers) in place for now; Phase 1.2
  consolidates them into `domain/services/library_layout.py`
- Ensure `domain/` imports only stdlib + external libraries + itself (no cross-layer
  imports)
- Update imports throughout codebase:
  - Search for imports of `records` module (e.g., `from audiolibrarian import records`)
  - Replace with new imports (e.g., `from audiolibrarian.domain.model import release`)
  - Update test files: search for `records` imports in `tests/` and update to new locations
- Run full test suite

**Why now**: The domain is the center of the hexagon; everything else will depend on it,
so it must be clean and dependency-free before we build outward.

**DDD concept taught**: Entity vs. Value Object, curing primitive obsession

**Learning checkpoint**: Which of my model classes carry identity and which are pure values,
and why? Where do the invariants actually live? (Answering this honestly is what led to the
Phase 1.1 revision.)

---

### Phase 1.1: Freeze the Metadata Model *(replaces "Release as Aggregate")*

> **This phase was originally "Implement Release as Aggregate with Invariants." It was
> revised after the evidence showed `Release` is not an aggregate root.** See
> *Why Release Is Not an Aggregate Root* below.

**Tasks**:

- Revert the aggregate-encapsulation experiment:
  - `Release._media` → `media` and `Medium._tracks` → `tracks` (public again)
  - Delete the `MappingProxyType` properties — they allocate a fresh proxy on every
    access and guard nothing, since nothing mutates the dicts anyway
  - Revert `tests/test__musicbrainz.py` to compare without reaching through private
    attributes (the encapsulation forced the tests to reach *around* it — the tell that it
    was protecting nothing)
- Add `frozen=True` to `Release`, `Track`, and `OneTrack` (`Medium` already has it). This is
  real protection at zero test cost: it makes aliasing surprises impossible.
- Convert the two genuine mutation sites to `attrs.evolve`:
  - `_audiosource.py` front-cover backfill →
    `self._release = attrs.evolve(self._release, front_cover=cover)`.
    This matters: the same `_release` instance is aliased across every `TagGateway` in the
    album via `Base._tag_files`.
  - `flac.py` / `m4a.py` / `mp3.py` `release_obj.source = Source.TAGS` → `attrs.evolve`
    **after** the `Release(...) or None` truthiness check. Passing `source=` into the
    constructor would break `Record.__bool__`, which reports falsy only when *every* field
    is `None`.
- Give `Release.get_medium` a single contract. It currently returns `None` when `media` is
  `None` but raises `KeyError` for a missing disc — pick one.
- Delete `Release.pp`. It has no production caller, and it calls `.tracks.items()` with no
  `None` guard. `Base._summary` does the real rendering, and Phase 4 moves that to
  `ConsoleUI`.
- Run full test suite and `mypy src/` (frozen classes will surface any assignment site the
  grep missed).

**Why now**: Phase 1 extracted the structure. This phase makes the metadata model genuinely
immutable — which is the protection that actually applies here — instead of adding aggregate
machinery for a consistency boundary that does not exist.

**DDD concept taught**: Immutability vs. encapsulation; recognizing when a pattern is
ceremony. Learning where a pattern is *not* worth its cost is a core DDD skill.

**Learning checkpoint**: What test would fail if `Release` were a true aggregate root that
does not fail today? Why is `frozen=True` protection, while `MappingProxyType` over a
public-by-convention dict is not?

---

### Why Release Is Not an Aggregate Root

An aggregate root is a **consistency boundary**: a cluster of objects that must always be
valid *together*, loaded and saved as a unit, mutated only through the root. `Release` meets
none of those conditions in this codebase:

- **Nothing mutates the collections.** There is no `del`, no item assignment, and no `.pop`
  against `media` or `tracks` anywhere in `src/`. A consistency boundary with no mutations
  has nothing to keep consistent.
- **No `Release` is ever loaded or saved as a unit.** `Base._write_manifest` hand-flattens
  13 scalar keys — no tracks, no people, no cover. `Reconvert` reads exactly two of them
  (`disc_number`, `disc_count`) and re-queries MusicBrainz over the network for everything
  else. There is no repository that returns a `Release` by identity.
- **The only invariant in the model is on a value object.** `MediumPosition` validates
  `1 ≤ number ≤ count` in `values.py`. `Release` protects nothing.
- **Disc selection is a read, not a mutation.** `Base` calls
  `release.get_medium(position_number=...)`; nothing ever removes media or tracks from a
  `Release`.

What `Release` actually is: **an immutable metadata description of one edition of an Album**,
built from one of two provenances — a MusicBrainz HTTP response, or the tags of an existing
audio file (`Source.TAGS`). It is consumed to compute paths, filenames, and tag payloads,
then discarded at process exit.

**This does not make it a DTO.** A DTO is a dumb carrier. `Release` owns real behavior — the
artist/album/disc naming policy — and that behavior is the most valuable domain logic in the
project. Phase 1.2 promotes it rather than demoting it.

An alternative plan (`alternate-ddd-refactoring-plan.md`) reached the correct conclusion
about the aggregate and then over-corrected: it demoted `Release` to a DTO, deleted
`LibraryRepository` on the grounds that nothing is persistent, and modeled the pipeline as
a `ConversionJob` *domain entity*. That over-correction is rejected. The reasons are recorded
in that document's header.

---

### Decision: The Manifest Is Provenance Only

The `Manifest.yaml` question is the same question as the aggregate question, so it is settled
here rather than deferred.

Today `Base._write_manifest` writes 13 keys and `Reconvert` reads exactly two
(`disc_number`, `disc_count`). Everything else — `album`, `artist`, `genre`, `date`,
`musicbrainz_info`, `source_info` — is **write-only**. `Reconvert` re-queries MusicBrainz
using search data read back out of the source FLAC tags.

Three options were considered: leave it as provenance, use `musicbrainz_info` to look the
release up by ID instead of fuzzy-searching, or round-trip a full `Release` so `reconvert`
works offline.

**Decision: the manifest is provenance only.**

- A *Manifest* records what a library entry was made **from** — source type, bitrate,
  MusicBrainz IDs, disc position — for human and forensic use.
- It is **not** a serialized `Release`, and it does not enable offline reconvert.
- `Reconvert` keeps re-querying MusicBrainz from source tags and keeps taking only
  `disc_number` / `disc_count` from the manifest.
- Do **not** trim the currently-unread keys. They cost nothing and their value is
  documentary.

**Consequence, and why it belongs in this plan**: this confirms that `Release` is not a
persistent entity. Had we chosen the third option, `Release` would gain a real repository and
a real lifecycle, and the original aggregate framing would have been at least partly correct.
Choosing provenance-only closes that door deliberately — which is what licenses Phase 1.1 to
remove the aggregate machinery instead of merely postponing it.

Update `docs/glossary.md` accordingly: the current entry claims the manifest is "the
persisted provenance of a `Release` in the `Library`, **enabling *Reconvert***," which
overstates what it does.

---

### Phase 1.2: Make Library Layout the Center of the Domain

This is the phase that replaces the value the aggregate pattern was supposed to provide.
**Library Layout is the real business rule set in this project** — where a track goes and
what it is called — and it is currently smeared across four sites with two disagreeing
sources of truth and a live bug.

**Tasks**:

- Create `domain/services/library_layout.py` as the single owner of:
  - the four format tree names (`flac` / `m4a` / `mp3` / `source`), currently bare string
    literals in `Base._move_files` and repeated in `Base._write_manifest`
  - artist/album directory naming (moved from `Release.get_artist_album_path`, still using
    `text.filename_from_title`)
  - **one** `discN` rule (see the divergence below)
  - track filenames (moved from `Track.get_filename`)
- Collapse the duplicate call sites onto the new service: `Base._move_files`,
  `Base._write_manifest`, `OneTrack.get_artist_album_disc_path`, and the two ad-hoc
  track-number re-parses in `Base._rename_wav` and `Base._tag_files` — both of which should
  use the existing `values.TrackNumber.from_filename`, currently unused in `src/`.
- Resolve `values.AudioFormat`, which is referenced only by tests today: either adopt it as
  the encoder/tree key here, or delete it.
- Add the two regression tests described below.
- Run full test suite.

**The `discN` divergence to fix**: there are two independent implementations of the same
decision, and they read from different sources.

<!-- pyml disable line-length -->
| Site                                                      | Decides `discN` from                                  |
|-----------------------------------------------------------|-------------------------------------------------------|
| `Base._move_files` (the write path)                       | `Base._multi_disc` — CLI `--disc` or manifest-derived |
| `OneTrack.get_artist_album_disc_path` (the `rename` path) | tag-derived `MediumPosition.count`                    |
<!-- pyml enable line-length -->

Because `rename` recomputes the layout from tags, any disagreement between these two means
`rename` will move files that `convert` just placed. One rule, one source of truth.

**The live bug to fix**: `Base._write_manifest` builds the album path **without** the `discN`
component, while `Base._move_files` puts multi-disc source files **into** `discN`. Every disc
of a multi-disc release therefore writes to the same
`source/Artist/YYYY__Album/Manifest.yaml`, one level above its own FLAC files — each disc
silently overwriting the last. Existing libraries keep working because `_find_manifests`
uses `rglob`; only newly written manifests land in the corrected location.

**Why now**: this is the highest-value extraction available, and it must land before Phase 3
builds `FilesystemLibraryRepository` — the repository should consume one layout rule, not
re-derive a third copy of it.

**DDD concept taught**: Domain Service; finding the real domain logic by looking for the
rules that are duplicated and disagreeing.

**Learning checkpoint**: The layout rules were split across `Release`, `OneTrack`, and
`Base`. Why did that split happen, and what made the manifest path bug invisible for so long?

---

### Phase 2: Declare the Ports; Reclassify Existing ABCs as Adapters

**Tasks**:

- Create the `application/ports/*` interfaces:
  - `metadata_provider.py` - MetadataProvider port
  - `audio_source.py` - AudioSource port (today's ABC becomes the interface)
  - `tag_gateway.py` - TagGateway port (today's TagGateway ABC)
  - `encoder.py` - Encoder port
  - `normalizer.py` - Normalizer port (today's ABC)
  - `library_repository.py` - LibraryRepository port
  - `user_interface.py` - UserInterface port
- Move existing ABCs to become the port interfaces
- Move concrete implementations to `infrastructure/` as adapters:
  - `CDAudioSource`, `FilesAudioSource` → `infrastructure/audiosources/`
  - `TagGateway` subclasses → `infrastructure/tags/`
  - `Normalizer` subclasses → `infrastructure/normalizers/`
- Update imports throughout codebase:
  - Search for imports of moved ABCs (e.g.,
    `from audiolibrarian.audiofile import AudioFile`)
  - Replace with port imports (e.g.,
    `from audiolibrarian.application.ports.tag_gateway import TagGateway`)
  - Update `Base` and command classes to use new import locations
- Run full test suite

**Why now**: With a clean domain, we can express what the core needs as interfaces before
touching the tangled `Base`.

**DDD concept taught**: Ports & Adapters, Dependency Inversion

**Learning checkpoint**: For each port, who "owns" the interface and who "conforms"? Which
way do the dependency arrows point, and why is that inverted from a naive design?

---

### Phase 3: Extract Infrastructure out of `Base`

**Tasks**:

- Pull `_make_flac`, `_make_m4a`, `_make_mp3` from `Base` into `Encoder` adapters:
  - Create `infrastructure/encoders/flac_encoder.py`
  - Create `infrastructure/encoders/m4a_encoder.py`
  - Create `infrastructure/encoders/mp3_encoder.py`
- Build `FilesystemLibraryRepository` in `infrastructure/library/`. **The library is read as
  well as written**, so this port is two-directional — the reads are currently scattered
  across four `rglob`/`glob` sites and belong here:

  - `path_for(release, medium_position, fmt)` — the path arithmetic in `_move_files` and
    `_write_manifest`, delegating the rules to Phase 1.2's `library_layout`
  - `store(...)` / `move(...)` — `Base._move_files` (`rmtree` + `Path.rename`)
  - `find_manifests(dirs)` — `Base._find_manifests`
  - `iter_audio_files(dirs)` — `Base._find_audio_files`
  - `prune_empty(path)` — the `glob`/`rmdir` walk inside the `Rename` command
  - `write_manifest(...)` / `read_manifest(...)` — `Base._write_manifest` / `_read_manifest`

  Note: `Path.rename` raises across filesystem boundaries. The repository is the right place
  to decide whether that becomes `shutil.move`.
- Wrap `musicbrainz.py` as the `MusicBrainzProvider` ACL behind `MetadataProvider`:
  - Create `infrastructure/musicbrainz/musicbrainz_provider.py`
  - Create `infrastructure/musicbrainz/musicbrainz_mapper.py`
  - Use Pydantic for DTOs at the MusicBrainz API boundary (validation/serialization)
- Update `Base` to use the new adapters
- Run full test suite

**Why now**: `Base` shrinks to pure orchestration once the "how" (infrastructure) is gone.

**DDD concept taught**: Repository, Anti-Corruption Layer

**Learning checkpoint**: What foreign concepts did the MusicBrainz ACL stop from leaking
inward? Name three.

---

### Phase 4: Extract Presentation

**Tasks**:

- Introduce `UserInterface` port in `application/ports/user_interface.py` with methods:
  - `confirm(summary) -> bool`
  - `prompt(message) -> str`
  - `show(message)`
  - `display_table(data)`
- Create `ConsoleUI` adapter in `presentation/console_ui.py`:
  - Implements UserInterface using print, `text.input_`, and table rendering
- Move `_summary` rendering from `Base` to `ConsoleUI`
- Move all `print`, `text.input_`, and confirm logic from `Base` to `ConsoleUI`
- Move prompts currently inside `musicbrainz.py` (e.g., "Genre not found") to use
  UserInterface
- Update `Base` to use UserInterface port
- Run full test suite

**Why now**: With I/O gone, the remaining `Base` logic is pure decisions (application
orchestration).

**DDD concept taught**: Keeping I/O at the edges; testability of a pure core

**Learning checkpoint**: Could I run a full "convert" in a unit test with zero real I/O? If
not, what's still leaking?

---

### Phase 5: Introduce Use Cases; Make Commands Thin

**Approach**: Migrate one use case/command at a time to maintain test-green status. Each
sub-phase converts one command to the new architecture.

#### Phase 5a: RipAlbum use case

- Create `application/use_cases/rip_album.py` with RipAlbum use case
- Move orchestration logic from `Rip.__init__` and `Base._convert`/`_get_tag_info` into use
  case
- Create request DTO as attrs class: `RipRequest(search_data, disc_position)`
- Rewrite `Rip` command as thin adapter using tyro
- Add factory functions to relevant adapter `__init__.py` files
- Add composition root function for RipAlbum in `presentation/cli/composition_root.py`
- Update CLI entry point to use new Rip command
- Run tests for rip command
- Commit: "refactor(app): add RipAlbum use case; convert Rip command to tyro"

#### Phase 5b: ConvertFiles use case

- Create `application/use_cases/convert_files.py` with ConvertFiles use case
- Move orchestration logic from `Convert.__init__` and `Base._convert`/`_get_tag_info` into
  use case
- Create request DTO as attrs class: `ConvertRequest(filenames, search_data,
  disc_position)`
- Rewrite `Convert` command as thin adapter using tyro
- Add composition root function for ConvertFiles
- Update CLI entry point
- Run tests for convert command
- Commit: "refactor(app): add ConvertFiles use case; convert Convert command to tyro"

#### Phase 5c: Remaining use cases

- Repeat pattern for: Reconvert, Rename, Manifest, Genre
- One use case per sub-phase
- Each sub-phase: create use case, rewrite command, add composition root, test, commit

#### Phase 5d: Cleanup

- Remove old `Base` orchestration methods now that all use cases exist
- Ensure all commands use tyro and composition root
- Run full test suite
- Commit: "refactor(app): complete use case migration; remove Base orchestration"

**Common tasks for each use case**:

- Define request DTO as attrs class with relevant fields
- Use tyro to parse CLI args into request object
- Use existing `config.Settings` (pydantic-settings) for configuration
- Adapter selection is compile-time based on command type
- Factory functions in adapter module `__init__.py` files:
  - `infrastructure/encoders/__init__.py`: `create_encoders()` returns tuple of
    (FlacEncoder, M4aEncoder, Mp3Encoder)
  - `infrastructure/tags/__init__.py`: `TagGateway()` auto-detects format from file
    extension
  - `infrastructure/normalizers/__init__.py`: `create_normalizer(settings)` wraps
    existing factory pattern
  - `infrastructure/audiosources/__init__.py`: `create_audio_source()` based on command
    type

**Why now**: The use case is the seam between "a human asked for X" and "here's how X
happens." Thin commands mean the CLI is just one trigger among possible many.

**DDD concept taught**: Application Service / Use Case, Composition Root, dependency
injection

**Learning checkpoint**: If I had to add a web UI tomorrow, which layers change and which
don't?

---

### Phase 6: Retire `Base`, Refocus Tests, Update Docs

**Tasks**:

- Delete `Base` class
- Delete `_audiosource.py` file
- Split tests into three categories:
  - **Domain tests**: No mocks, pure objects testing invariants and value object behavior
  - **Use-case tests**: With fake adapters, testing orchestration
  - **Adapter tests**: Integration tests with real dependencies
- Update `docs/` and `README` to describe the layered architecture
- Update any remaining documentation to reflect new structure
- Run full regression test suite
- Verify import-linter contract still passes
- Clean up any remaining TODO comments or temporary files

**Why last**: You only remove the scaffold once the new structure carries the weight.

**DDD concept taught**: The testing pyramid that hexagonal architecture unlocks

**Learning checkpoint**: Which deferred pattern (from ADR 0002) is the first I'd expect to
actually need, and what would trigger it?

---

## Suggested Commit Sequence

```text
chore(ddd): add glossary + layer skeleton + import-linter contract    (Phase 0)
refactor(domain): extract pure domain model + value objects           (Phase 1)
refactor(domain): freeze the metadata model; drop aggregate ceremony  (Phase 1.1)
refactor(domain): consolidate library layout rules; fix manifest path (Phase 1.2)
refactor(app): define ports; move AudioSource/TagGateway/Normalizer   (Phase 2)
refactor(infra): extract encoders, library repository, MB ACL         (Phase 3)
refactor(ui): introduce UserInterface + ConsoleUI                     (Phase 4)
refactor(app): add RipAlbum use case; convert Rip command to tyro     (Phase 5a)
refactor(app): add ConvertFiles use case; convert Convert command     (Phase 5b)
refactor(app): add remaining use cases; convert remaining commands    (Phase 5c)
refactor(app): complete use case migration; remove Base orchestration (Phase 5d)
refactor: remove Base; restructure tests; update docs                 (Phase 6)
```

Each commit is independently reviewable and leaves `pytest` green.

## Patterns Deferred (for future reference)

The following patterns are deliberately deferred until the pain they solve is actually
felt:

- Domain Events
  - Why deferred: No subscribers exist; nothing reacts asynchronously. Pure ceremony.
  - Adopt when: You add side effects (notify, index, sync) that shouldn't be
    hard-wired into use cases.

- Factories as objects
  - Why deferred: The ACL already is the construction logic; a separate class adds
    indirection.
  - Adopt when: Construction rules get complex enough to reuse/test independently.

- Formal Domain Services
  - Why deferred: Plain functions in `domain/services/` are enough and simpler.
  - Adopt when: Logic grows state or multiple collaborating strategies.

- Unit of Work / transactions
  - Why deferred: Filesystem work-dir + move already gives crude atomicity; single
    user, no concurrency.
  - Adopt when: Partial-failure corruption becomes a real problem.

- Specification pattern
  - Why deferred: One fuzzy-match rule; a helper function suffices.
  - Adopt when: Matching rules multiply and need to combine.

- CQRS
  - Why deferred: The app is essentially all "commands" already; no read-scaling
    need.
  - Adopt when: Query needs diverge sharply from write needs.

- Multiple Bounded Contexts
  - Why deferred: One language, one dev - no linguistic strain.
  - Adopt when: Language conflicts or team boundaries emerge.

## Success Criteria

The refactoring is complete when:

- [ ] All phases are completed (0, 1, 1.1, 1.2, 2–6)
- [ ] `Base` class is removed
- [ ] All tests pass with new structure
- [ ] Import-linter contract passes
- [ ] Domain layer has no external dependencies
- [ ] All I/O is behind ports
- [ ] CLI commands are thin adapters
- [ ] Documentation is updated
- [ ] Learning checkpoints are answered

Phase-1.1/1.2-specific criteria:

- [ ] `Release`, `Medium`, `Track`, `OneTrack` are all frozen; no attribute assignment
      remains anywhere in `src/`
- [ ] Exactly one implementation of the `discN` rule, one definition of the four format tree
      names, and one track-number parser
- [ ] A two-disc release writes one `Manifest.yaml` per disc, alongside that disc's files
- [ ] **The end-to-end proof**: run `audiolibrarian convert` on a real two-disc album, then
      `audiolibrarian rename --dry-run` over the result. It must report **no** renames. The
      write path and the read path computing identical layouts is the whole point of Phase
      1.2, and this is the cheapest way to verify it.
