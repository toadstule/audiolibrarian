# Alternate DDD Refactoring Plan (Pipeline-Focused Approach)

> ## Status: REJECTED — retained as a design record
>
> This plan was written mid-migration, when implementing "Release as an aggregate root"
> stopped feeling right. **Its core observation was correct and has been adopted.** Its
> proposed architecture was not.
>
> ### What was right, and was adopted
>
> `Release` is not an aggregate root. Verified against the code: nothing mutates `media` or
> `tracks` anywhere in `src/`; no `Release` is ever loaded or saved by identity (the manifest
> writes 13 flat keys and `reconvert` reads two of them, then re-queries MusicBrainz); and the
> model's only invariant lives on the `MediumPosition` value object. The aggregate phase was
> therefore ceremony, and it had already made `tests/test__musicbrainz.py` reach *through* the
> private attributes it introduced.
>
> This became **Phase 1.1 (Freeze the Metadata Model)** and **Phase 1.2 (Make Library Layout
> the Centre of the Domain)** in `ddd-refactoring-plan.md`, plus the settled decision that the
> manifest is provenance only.
>
> ### Why the rest was rejected
>
> 1. **"No persistence, no repository" is false.** The library tree *is* the persistence and
>    the tags *are* the serialization format. Every `AudioFile.open()` reconstitutes a full
>    Release → Medium → Track → OneTrack graph from tags, and `rename` runs entirely on that
>    with no network at all. That is load-from-storage → recompute → write-back. Deleting
>    `LibraryRepository` does not remove those reads; it leaves them scattered across four
>    `rglob` sites inside `Base`.
> 2. **`ConversionJob` as a domain entity rebuilds `Base` under a DDD name.** A thing that
>    tracks state across rip → normalize → encode → tag → move is an *application service*. In
>    `domain/model/` it will need work directories and subprocess ordering — exactly the
>    layer fusion this migration exists to undo, but now blessed by the import-linter because
>    it is nominally "domain".
> 3. **`AudioSource` as a domain entity demotes a working abstraction.** It is already a
>    correct port with two adapters. This plan lists both `domain/model/audio_source.py` *and*
>    `application/ports/audio_source.py` — two different things sharing one name, in a plan
>    whose Phase 0 is about ubiquitous language.
> 4. **It silently drops `rename`.** The use-case list omits it. `rename` is the most
>    domain-heavy command in the project: pure layout policy applied to metadata
>    reconstituted from tags, no network, no encoding. Losing it is a direct consequence of
>    deciding the library is not part of the domain.
> 5. **Release-as-DTO discards the only real behavior in the model.**
>    `get_artist_album_path`, `get_artist_album_disc_path`, and `get_filename` *are* the
>    naming policy. Re-expressing them as free functions over a DTO makes the model more
>    anemic, not less.
>
> ### The reframe that resolved it
>
> This domain has **two** concepts, and this document and the original plan each captured one:
>
> - **Release** — an immutable metadata description with two provenances (MusicBrainz, file
>   tags). Not an aggregate root (this document was right), but not a DTO either (the original
>   plan was right that it owns behavior).
> - **Library Layout** — the actual business rules, currently smeared across four sites with
>   two disagreeing sources of truth for the `discN` decision and a live bug that makes
>   multi-disc manifests overwrite one another.
>
> The pipeline is an application service. This document identified the right *centre of
> gravity* — the tool is about getting files into a correct layout — and then filed it in the
> wrong layer.

## Core Insight

**Current plan assumes**: audiolibrarian is a library management system where Release is the central
domain entity with lifecycle, invariants, and aggregate behavior.

**Actual purpose**: audiolibrarian is a pipeline tool that:

1. Takes audio sources (CD or files)
2. Fetches metadata from MusicBrainz
3. Converts/tag files using that metadata
4. Organizes output into a library structure

**Key observation**: Release is transient metadata fetched from MusicBrainz, applied to files, then
discarded. There's no Release repository, no persistence, no lifecycle management. The "domain" is
the conversion pipeline itself.

## Target Architecture (Pipeline-Focused)

### Domain Layer

Contains pure business logic about the conversion pipeline and library organization rules.

```text
src/audiolibrarian/domain/
├── __init__.py
├── model/
│   ├── __init__.py
│   ├── audio_source.py     # AudioSource entity (CD, files)              [entity]
│   ├── conversion_job.py   # ConversionJob entity (tracks the process)    [entity]
│   ├── library_layout.py   # LibraryLayout value object (path rules)      [value object]
│   ├── metadata.py         # ReleaseMetadata DTO (from MusicBrainz)       [DTO]
│   ├── values.py           # TrackNumber, AudioFormat, FileInfo, etc.     [value objects]
│   └── enums.py            # BitrateMode, FileFormat, Source                [enums]
└── services/
    ├── __init__.py
    ├── source_matching.py  # match source files → track metadata
    ├── path_builder.py     # construct library paths from metadata
    └── validation.py       # validate source vs metadata consistency
```

### Application Layer

Orchestrates the pipeline steps. Defines ports for external dependencies.

```text
src/audiolibrarian/application/
├── __init__.py
├── ports/
│   ├── __init__.py
│   ├── metadata_provider.py    # MusicBrainz API (ACL)
│   ├── audio_source.py         # CD reader, file scanner
│   ├── tag_gateway.py          # read/write tags
│   ├── encoder.py              # audio encoders
│   ├── normalizer.py           # audio normalization
│   └── user_interface.py       # prompts, confirmations
└── use_cases/
    ├── __init__.py
    ├── rip_and_convert.py      # CD → library pipeline
    ├── convert_files.py        # files → library pipeline
    ├── reconvert_library.py    # reconvert existing library files
    ├── manage_genres.py        # MusicBrainz genre preferences
    └── write_manifest.py       # generate manifest files
```

### Infrastructure Layer

Implements port interfaces as adapters.

```text
src/audiolibrarian/infrastructure/
├── __init__.py
├── musicbrainz/            # ACL: implements MetadataProvider
│   ├── __init__.py
│   ├── musicbrainz_client.py
│   └── metadata_mapper.py   # MB API → ReleaseMetadata DTO
├── audiosources/           # CD + file adapters
│   ├── __init__.py
│   ├── cd_ripper.py
│   └── file_scanner.py
├── tags/                   # FLAC/M4A/MP3 tag adapters
│   ├── __init__.py
│   ├── flac_tagger.py
│   ├── m4a_tagger.py
│   └── mp3_tagger.py
├── encoders/               # audio encoders
│   ├── __init__.py
│   ├── flac_encoder.py
│   ├── m4a_encoder.py
│   └── mp3_encoder.py
└── normalizers/            # audio normalizers
    ├── __init__.py
    ├── ffmpeg_normalizer.py
    └── wavegain_normalizer.py
```

### Presentation Layer

CLI-specific code and composition root.

```text
src/audiolibrarian/presentation/
├── __init__.py
├── cli/
│   ├── __init__.py
│   ├── command_handlers.py
│   └── composition_root.py
└── console_ui.py
```

## Key Differences from Current Plan

### Domain Model

**Current plan**: Release as aggregate root with Medium/Track entities

- Assumes Release is the core entity being managed
- Implements aggregate pattern with invariants
- Release has lifecycle and mutation methods

**Alternate plan**: Pipeline-focused domain

- AudioSource as input entity
- ConversionJob as process tracker
- ReleaseMetadata as DTO from MusicBrainz ACL
- No Release aggregate - it's external data we consume

### Architecture Layers

**Current plan**: Full hexagonal with library repository

- Assumes persistent Release entities
- LibraryRepository for managing releases
- More complex than needed

**Alternate plan**: Pipeline-focused hexagonal

- No repository layer (no persistent entities)
- Focus on pipeline orchestration
- Simpler, matches actual usage

### Use Cases

**Current plan**: Library management use cases

- rip_album, convert_files, reconvert_library, rename_library
- Assumes library of releases to manage

**Alternate plan**: Pipeline use cases

- rip_and_convert (single pipeline)
- convert_files (single pipeline)
- reconvert_library (reconvert existing library files)
- manage_genres (setup step for metadata preferences)
- write_manifest (output generation)

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
│   │   │   ├── test_audio_source.py
│   │   │   ├── test_conversion_job.py
│   │   │   ├── test_library_layout.py
│   │   │   ├── test_metadata.py
│   │   │   └── test_values.py
│   │   └── services/
│   │       ├── test_source_matching.py
│   │       ├── test_path_builder.py
│   │       └── test_validation.py
│   └── application/
│       ├── test_rip_and_convert.py
│       ├── test_convert_files.py
│       ├── test_reconvert_library.py
│       ├── test_manage_genres.py
│       └── test_write_manifest.py
├── integration/
│   ├── infrastructure/
│   │   ├── test_musicbrainz_client.py
│   │   ├── test_cd_ripper.py
│   │   ├── test_file_scanner.py
│   │   ├── test_taggers.py
│   │   ├── test_encoders.py
│   │   └── test_normalizers.py
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

#### Phase 1: Extract Pipeline Domain Model

- Write unit tests for each new value object before implementation
- Test invariants (e.g., TrackNumber formatting, AudioFormat validation)
- Ensure existing tests still pass after moving entities
- Add domain tests for AudioSource and ConversionJob behavior
- Test that value objects are immutable (frozen dataclass)
- Test that ReleaseMetadata DTOs correctly represent external data

#### Phase 2: Define Ports for Pipeline

- Write unit tests for port interfaces using test doubles
- Ensure existing tests still pass after defining interfaces
- Test that port contracts are clear and complete
- Add integration tests for accidental ports (AudioSource, Normalizer, TagGateway)

#### Phase 3: Extract Infrastructure Adapters

- Write integration tests for MusicBrainz ACL using pytest-vcr to record/replay API
  responses
- Test encoder adapters with real subprocess calls in integration suite
- Test tagger adapters with real file I/O in integration suite
- Test that infrastructure has no dependencies on application/presentation
- Test that adapters correctly implement port interfaces

#### Phase 4: Extract Use Cases

- Write unit tests for use cases using fake adapters
- Test orchestration logic (correct sequence of adapter calls)
- Test error handling in use cases
- Ensure existing tests still pass after extracting use cases

#### Phase 5: Extract Presentation

- Write unit tests for UserInterface port using test doubles
- Write integration tests for ConsoleUI adapter
- Ensure all I/O is behind the port (no print/input in core)
- Test that prompts and summaries render correctly
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
  `AudioSource(source_type="CD", ...)`)
- Add factory_boy later if test setup becomes repetitive
- Ensure test data is isolated and doesn't leak between tests

### Coverage Goals

- Maintain current coverage levels throughout migration
- Target 80%+ coverage for new domain layer code
- Focus coverage on business-critical paths (pipeline orchestration)
- Use `pytest-cov` to generate coverage reports

## Migration Phases

### Phase 0: Language & Guardrails *(no behavior change)*

**Tasks**:

- Write ubiquitous language glossary into `docs/glossary.md` focused on pipeline concepts:
  - Audio Source, Conversion Job, Metadata, Library Layout
- Create empty layer skeleton with `__init__.py` files
- Add import-linter contract enforcing dependency rule
- Add pytest-vcr for MusicBrainz API testing
- Run full test suite

**Why first**: Establish the language and dependency rule before making architectural decisions.

**DDD concept taught**: Ubiquitous Language, Dependency Rule

**Learning checkpoint**: Why is the dependency rule important? What happens if it's violated?

---

### Phase 1: Extract Pipeline Domain Model

**Tasks**:

- Move `records.py` content into `domain/model/` split into:
  - `audio_source.py` - AudioSource entity (represents CD or file input)
  - `conversion_job.py` - ConversionJob entity (tracks pipeline state)
  - `metadata.py` - ReleaseMetadata DTO (data from MusicBrainz)
  - `values.py` - existing value objects (TrackNumber, AudioFormat, etc.)
  - `enums.py` - existing enums
- Move Release/Medium/Track to `metadata.py` as DTOs (not entities)
- Freeze value objects with `@attr.frozen=True`
- Create `library_layout.py` value object for path rules
- Ensure `domain/` imports only stdlib + external libraries + itself
- Update imports throughout codebase
- Run full test suite

**Why now**: Extract the actual domain concepts (pipeline) rather than forcing Release as an entity.

**DDD concept taught**: DTO vs Entity, Pipeline as domain

**Learning checkpoint**: What's the difference between an entity and a DTO? Why is Release a DTO here?

---

### Phase 2: Define Ports for Pipeline

**Tasks**:

- Define port interfaces in `application/ports/`:
  - `MetadataProvider` - fetch release metadata from MusicBrainz
  - `AudioSource` - read audio from CD or files
  - `TagGateway` - read/write audio file tags
  - `Encoder` - convert audio formats
  - `Normalizer` - normalize audio levels
  - `UserInterface` - prompts and confirmations
- Write unit tests for port interfaces using test doubles
- Ensure ports have no dependencies on infrastructure
- Run full test suite

**Why now**: Define the boundaries before implementing adapters.

**DDD concept taught**: Ports & Adapters, Dependency Inversion

**Learning checkpoint**: Why do we define ports in the application layer, not infrastructure?

---

### Phase 3: Extract Infrastructure Adapters

**Tasks**:

- Move MusicBrainz code to `infrastructure/musicbrainz/` implementing `MetadataProvider`
- Move audio source code to `infrastructure/audiosources/` implementing `AudioSource`
- Move tag code to `infrastructure/tags/` implementing `TagGateway`
- Move encoder code to `infrastructure/encoders/` implementing `Encoder`
- Move normalizer code to `infrastructure/normalizers/` implementing `Normalizer`
- Write integration tests for each adapter
- Ensure infrastructure has no dependencies on application/presentation
- Run full test suite

**Why now**: Implement the adapters that fulfill the port contracts.

**DDD concept taught**: Anti-Corruption Layer (MusicBrainz), Adapters

**Learning checkpoint**: What does the MusicBrainz ACL protect us from?

---

### Phase 4: Extract Use Cases

**Tasks**:

- Create `application/use_cases/rip_and_convert.py` orchestrating the CD pipeline
- Create `application/use_cases/convert_files.py` orchestrating the file pipeline
- Create `application/use_cases/manage_genres.py` for MusicBrainz genre preferences
- Create `application/use_cases/write_manifest.py` for manifest generation
- Write unit tests for use cases using fake adapters
- Move orchestration logic from `Base` to use cases
- Run full test suite

**Why now**: Extract the actual business workflows as application services.

**DDD concept taught**: Application Service, Use Case

**Learning checkpoint**: What's the difference between domain logic and application logic?

---

### Phase 5: Extract Presentation

**Tasks**:

- Move CLI code to `presentation/cli/`
- Create `composition_root.py` wiring dependencies
- Implement `ConsoleUI` for `UserInterface` port
- Ensure all I/O is behind the port
- Test that commands work as before (regression testing)
- Run full test suite

**Why now**: Separate presentation concerns from application logic.

**DDD concept taught**: Composition Root, Presentation Layer

**Learning checkpoint**: Why is the composition root in presentation, not application?

---

### Phase 6: Retire Base

**Tasks**:

- Remove `Base` class
- Restructure tests into domain/use-case/adapter categories
- Verify all import-linter contracts pass
- Run full regression test suite
- Update documentation

**Why now**: Clean up the old architecture after migration is complete.

**Learning checkpoint**: What did we gain from this refactoring?

## Suggested Commit Sequence

```text
chore(ddd): add glossary + layer skeleton + import-linter contract    (Phase 0)
refactor(domain): extract pipeline domain model + DTOs                 (Phase 1)
refactor(app): define ports for pipeline                               (Phase 2)
refactor(infra): extract adapters (MB, sources, tags, encoders)        (Phase 3)
refactor(app): extract use cases (pipeline orchestration)               (Phase 4)
refactor(ui): extract CLI + composition root                           (Phase 5)
refactor: remove Base; restructure tests; update docs                  (Phase 6)
```

## Trade-offs

### Pros of This Approach

- **Matches actual usage**: Domain model reflects the pipeline nature of the app
- **Simpler**: No unnecessary aggregate pattern for transient data
- **Clear boundaries**: DTOs clearly separate external data from domain logic
- **Easier to understand**: Pipeline focus is more intuitive than Release-centric model

### Cons of This Approach

- **Less "textbook DDD"**: Doesn't follow the standard aggregate pattern
- **Genre command is separate**: Genre management doesn't fit neatly into pipeline model
- **May need adjustment**: If the app evolves toward library management, domain may need refactoring

### What Would Revive This Plan

Nothing about the pipeline framing, which is already reflected in the use-case layer. But two
specific changes would reopen the questions this document raised:

- **If the manifest became a full serialized `Release`** so that `reconvert` worked offline,
  `Release` would gain a genuine repository and lifecycle — and the aggregate framing this
  document argued against would become at least partly correct. That option was considered and
  rejected in favour of provenance-only; see *Decision: The Manifest Is Provenance Only* in
  `ddd-refactoring-plan.md`.
- **If library management features arrived** (browsing, searching, editing releases in place),
  `Release` would need identity and mutation, and the aggregate pattern would earn its cost.

### The Lesson Worth Keeping

Both documents were written before anyone checked whether `Release` was ever mutated,
persisted, or loaded by identity. It is not, on all three counts — a five-minute grep. The
original plan asserted an aggregate; this document asserted a DTO; the code said "immutable
description, and by the way your real rules are duplicated four ways with a bug in them."

DDD done well is reactive: feel the pain, then name the cure. Both of these named cures first.
