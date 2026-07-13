# 2. Adopt Domain-Driven Design (Pragmatic Hexagonal Architecture)

## Status
Proposed

## Context
The audiolibrarian codebase has grown organically with business logic scattered across multiple modules. The current architecture has several characteristics that make it difficult to maintain and extend:

- **Anemic domain model**: Entities in `records.py` are primarily data containers with minimal behavior
- **Scattered business logic**: Domain rules are spread across `base.py`, `commands.py`, and various service classes
- **Mixed concerns**: The `Base` class orchestrates workflows but also contains domain logic
- **No clear boundaries**: It's difficult to identify where one domain concept ends and another begins
- **Direct infrastructure coupling**: File system operations and external API calls are interleaved with domain logic
- **Missing abstractions**: No repository pattern for persistence, no domain events for cross-cutting concerns
- **God class**: `Base` mixes domain, application, infrastructure, and presentation layers
- **Primitive obsession**: Disc positions and track numbers are primitive strings/ints with scattered validation
- **I/O in the core**: `print()`, `text.input_()`, and subprocess calls live inside orchestration logic

As the project evolves, these issues will likely compound, making the codebase harder to understand, test, and modify.

## Decision
We will adopt Domain-Driven Design (DDD) principles using a **pragmatic hexagonal architecture** approach. This means:

- **Single bounded context**: One context for the entire application (appropriate for current scale and team size)
- **Four-layer architecture**: Presentation, Application, Domain, Infrastructure with dependency rule (arrows point inward)
- **Ports & Adapters**: Core defines ports (interfaces) in application layer; infrastructure provides adapters
- **Incremental migration**: Strangler pattern approach with test-green phases
- **Learning-oriented**: Educational focus with clear explanations of "why" each pattern matters
- **Pragmatic deferral**: Advanced patterns (domain events, CQRS, etc.) deferred until actually needed

### Bounded Context

**Single Context**: Music Library Management

For a project of this scale (~4,000 LOC, single developer), one bounded context is appropriate. Bounded contexts are a response to linguistic and organizational strain, not code size. The Anti-Corruption Layer provides the isolation benefit that multiple contexts would provide, without the integration overhead.

### Layered Architecture

The codebase will be restructured into four layers with the dependency rule: arrows point inward only.

```
presentation ─┐          (CLI, console UI: the "driving" adapters)
              ▼
        application  ───►  domain      (use cases orchestrate; domain holds rules)
              ▲
infrastructure┘          (MusicBrainz, codecs, filesystem: the "driven" adapters)
```

**Domain Layer** (`src/audiolibrarian/domain/`)
- Pure business logic with no infrastructure concerns
- Entities, value objects, domain services
- No imports from other layers (application, infrastructure, presentation)
- May import external libraries (e.g., attrs for data classes) but not internal project code

**Application Layer** (`src/audiolibrarian/application/`)
- Orchestrates domain objects to fulfill use cases
- Defines ports (interfaces) that the core needs
- Use cases (application services) - thin orchestration with no business rules
- Dependencies point inward: depends on domain, not infrastructure

**Infrastructure Layer** (`src/audiolibrarian/infrastructure/`)
- Implements port interfaces as adapters
- External service integrations (MusicBrainz, file system, encoders, normalizers)
- CLI adapters

**Presentation Layer** (`src/audiolibrarian/presentation/`)
- CLI-specific code (tyro for argument parsing, command adapters)
- Composition root that wires concrete adapters into use cases
- Console UI implementation
- CLI requests defined as attrs classes; tyro handles argument parsing

### Target Package Structure

```
src/audiolibrarian/
  domain/
    model/
      release.py        # Release (root), Medium, Track            [entities]
      values.py         # FrontCover, FileInfo, Performer, People,
                        # DiscPosition, TrackNumber, AudioFormat    [value objects]
      enums.py          # BitrateMode, FileType, Source
    services/
      source_matching.py  # match source files → tracks; count invariant
      library_layout.py   # artist/album/disc path rules
  application/
    ports/              # interfaces the core needs (abstractions it OWNS)
      metadata_provider.py
      audio_source.py
      tag_gateway.py       # read/write tags (today's AudioFile ABC)
      encoder.py
      normalizer.py
      library_repository.py
      user_interface.py    # prompts, confirmations, summaries
    use_cases/          # application services (thin orchestration)
      rip_album.py
      convert_files.py
      reconvert_library.py
      rename_library.py
      write_manifest.py
      manage_genre.py
  infrastructure/
    musicbrainz/        # ACL: implements MetadataProvider
    audiosources/       # CD + Files adapters
    tags/               # FLAC/M4A/MP3 tag adapters
    encoders/           # flac/m4a/mp3 encoder adapters (from Base._make_*)
    normalizers/        # ffmpeg/wavegain adapters
    library/            # FilesystemLibraryRepository + manifest persistence
    shell.py            # today's sh.py
  presentation/
    cli/                # argparse + thin command adapters + composition root
    console_ui.py       # implements UserInterface (print/input/summary table)
  config.py             # cross-cutting configuration
```

### Domain Model Design

**Entities** (identity, lifecycle):
- `Release` (id = MusicBrainz release id) - aggregate root, represents a specific edition of an Album
- `Medium` (id = medium number within its Release) - one physical or digital media unit within a Release
- `Track` (id = track number / MB track id within its Medium)

**Album Concept**:
- `Album` is a conceptual work (e.g., "Dark Side of the Moon")
- A `Release` belongs to an `Album` and references it via `album_name` and `album_id` (MusicBrainz release-group-id)
- `Release` remains the aggregate root; Album is a reference concept, not a separate entity
- This aligns with ubiquitous language (users say "album") while keeping the model simple

**Medium Presentation**:
- Domain model uses precise term `Medium` (aligns with MusicBrainz industry standard)
- UI and library paths use format-specific language for user-friendliness:
  - CD: "disc 1 of 2"
  - Vinyl/Cassette: "side 1 of 2"
  - Digital: no disc/side designation (just the album)

**Value Objects** (immutable, compared by value):
- Existing: `FrontCover`, `FileInfo`, `Performer`, `People`
- New to cure primitive obsession:
  - `DiscPosition(number, count)` - validates `1 ≤ number ≤ count` once, replaces `"x/y"` string
  - `TrackNumber(int)` - knows how to render as `"02"` and parse from filename
  - `AudioFormat` - FLAC/M4A/MP3 as first-class concept
- Implementation: Use `@attr.frozen=True` for immutability and ergonomics (attrs is already a project dependency)
- DTOs at infrastructure boundaries (e.g., MusicBrainz API responses) use Pydantic for validation/serialization

**Aggregate & Invariants**:
- `Release` is the aggregate root; `Medium` and `Track` reached only through it
- Root enforces invariants: track numbers unique/contiguous, source file count matches track count

**Domain Services**:
- Logic that doesn't naturally belong to one entity (e.g., matching ripped files to tracks)
- Plain functions in `domain/services/` (simpler than formal classes)

### Ports & Adapters

| Port (in `application/ports`) | Method(s) the core needs                                      | Adapter(s) (in `infrastructure`/`presentation`) | Source today                                  |
|-------------------------------|---------------------------------------------------------------|-------------------------------------------------|-----------------------------------------------|
| `MetadataProvider`            | `find_release(criteria) -> Release`                           | `MusicBrainzProvider` (**ACL**)                 | `musicbrainz.Searcher` + `MusicBrainzRelease` |
| `AudioSource`                 | `prepare()`, `wav_files()`, `search_hints()`, `front_cover()` | `CdAudioSource`, `FilesAudioSource`             | already an ABC                                |
| `TagGateway`                  | `read(path) -> OneTrack`, `write(path, one_track)`            | FLAC/M4A/MP3                                    | today's `AudioFile` ABC                       |
| `Encoder`                     | `encode(wavs, fmt, dest)`                                     | `FlacEncoder`, `M4aEncoder`, `Mp3Encoder`       | `Base._make_flac/_make_m4a/_make_mp3`         |
| `Normalizer`                  | `normalize(wavs)`                                             | ffmpeg / wavegain                               | already an ABC                                |
| `LibraryRepository`           | `store(release, media, files)`, `path_for(release)`           | `FilesystemLibraryRepository`                   | `Base._move_files`, `get_artist_album_path`   |
| `UserInterface`               | `confirm(summary)`, `prompt(...)`, `show(...)`                | `ConsoleUI`                                     | `print`, `text.input_`, `Base._summary`       |

**Key Principle**: Ports live in `application`, not `infrastructure`. The core owns the interface for what it needs; infrastructure conforms to it. This is the Dependency Inversion Principle.

### Anti-Corruption Layer

MusicBrainz's JSON has its own concepts (`artist-credit-phrase`, `medium-list`, `release-group`) and quirks (rate limits, `cdstub`s, missing dates). The Anti-Corruption Layer (ACL) translates the foreign model into our `Release` and absorbs the mess. This prevents MusicBrainz's model from leaking into and corrupting our domain model.

### Ubiquitous Language

Agreed terminology to use verbatim in code, tests, docs, and commit messages:

- **Album** — The conceptual work (e.g., "Dark Side of the Moon"). A Release belongs to an Album.
- **Release** — A specific edition of an Album (e.g., 1973 UK LP, 1992 CD remaster) as identified in MusicBrainz. *Aggregate root.* Contains references to its Album via `album_name` and `album_id`.
- **Medium** — One physical or digital media unit within a Release (what users commonly call "disc" for CDs, "side" for vinyl/cassettes, or just "the album" for digital). Has a `media_type` (CD, LP, Cassette, Digital) and `position` (e.g., "1 of 2"). The domain model uses "Medium" for precision; UI and library paths use format-specific language ("disc", "side", etc.) for user-friendliness.
- **Track** — one song on a `Medium`.
- **Performer / People** — credited contributors (value objects).
- **Front Cover** — cover art (value object).
- **Source Audio** — the input to be cataloged: a CD or existing files.
- **Library** — the organized, tagged destination (the `flac`/`m4a`/`mp3`/`source` trees). *Repository.*
- **Manifest** — the persisted provenance of a `Release` in the `Library`, enabling *Reconvert*.
- **Rip / Convert / Reconvert / Rename / Manifest / Genre** — the use cases.
- **Metadata Provider** — the source of truth for identification (MusicBrainz).
- **Encoder / Normalizer** — transcoding and loudness services.

### Architecture Enforcement

An import-linter contract will enforce the dependency rule: domain imports nothing from other layers. This makes the architecture executable - violations fail CI instead of rotting silently.

### Patterns Deferred (and Why)

Advanced DDD patterns are deliberately deferred until the pain they solve is actually felt:

| Pattern                         | Why Deferred                                                                           | Adopt When…                                                                             |
|---------------------------------|----------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------|
| **Domain Events**               | No subscribers exist; nothing reacts asynchronously. Pure ceremony.                    | You add side effects (notify, index, sync) that shouldn't be hard-wired into use cases. |
| **Factories as objects**        | The ACL already is the construction logic; a separate class adds indirection.          | Construction rules get complex enough to reuse/test independently.                      |
| **Formal Domain Services**      | Plain functions in `domain/services/` are enough and simpler.                          | Logic grows state or multiple collaborating strategies.                                 |
| **Unit of Work / transactions** | Filesystem work-dir + move already gives crude atomicity; single user, no concurrency. | Partial-failure corruption becomes a real problem.                                      |
| **Specification pattern**       | One fuzzy-match rule; a helper function suffices.                                      | Matching rules multiply and need to combine.                                            |
| **CQRS**                        | The app is essentially all "commands" already; no read-scaling need.                   | Query needs diverge sharply from write needs.                                           |
| **Multiple Bounded Contexts**   | One language, one dev - no linguistic strain.                                          | Language conflicts or team boundaries emerge.                                           |

## Migration Strategy

This will be an incremental migration using the strangler pattern. Each phase is a separate PR/commit that keeps the test suite green. We grow the new structure alongside the old and retire `Base` last.

**Ground rule for every phase**: run `pytest` (and `mypy`/`ruff`) before and after. If behavior changes, it's a bug, not a refactor. Add characterization tests first wherever current behavior isn't already covered.

### Phase 0: Language & Guardrails *(no behavior change)*
- Write the ubiquitous language glossary into `docs/`
- Create the empty `domain/ application/ infrastructure/ presentation/` skeleton
- Add import-linter contract enforcing the dependency rule (domain imports nothing from other layers)
- **Why first**: The language and dependency rule make every later decision obvious. The linter makes architecture executable.

### Phase 1: Purify the Domain Model
- Move `records.py` into `domain/model/` split into `release.py` / `values.py` / `enums.py`
- Freeze value objects with `@dataclass(frozen=True)`
- Introduce `DiscPosition`, `TrackNumber`, `AudioFormat` to cure primitive obsession
- Keep existing behavior methods (`get_filename`, path helpers)
- Move path helpers to `domain/services/library_layout.py` if they reference filesystem-layout rules
- Ensure `domain/` imports only stdlib + itself
- **Why now**: The domain is the center of the hexagon; everything else will depend on it.

### Phase 2: Declare the Ports; Reclassify Accidental Ports as Adapters
- Create the `application/ports/*` interfaces
- Move `AudioSource`, `AudioFile`→`TagGateway`, `Normalizer` under the new port definitions
- The ABCs become the ports; concrete classes move to `infrastructure/` as adapters
- **Why now**: With a clean domain, we can express what the core needs as interfaces before touching tangled `Base`.

### Phase 3: Extract Infrastructure out of `Base`
- Pull `_make_flac/_make_m4a/_make_mp3` into `Encoder` adapters
- Pull `_move_files`, `get_artist_album_path`, `_write_manifest`/`_read_manifest` into `FilesystemLibraryRepository`
- Wrap `musicbrainz.py` as the `MusicBrainzProvider` ACL behind `MetadataProvider`
- **Why now**: `Base` shrinks to pure orchestration once the "how" is gone.

### Phase 4: Extract Presentation
- Introduce `UserInterface` + `ConsoleUI`
- Move `_summary` rendering and all `print`/`text.input_`/confirm logic there
- Move prompts currently inside `musicbrainz.py` (e.g., "Genre not found")
- **Why now**: With I/O gone, the remaining `Base` logic is pure decisions.

### Phase 5: Introduce Use Cases; Make Commands Thin
- Create `application/use_cases/*` (`RipAlbum`, `ConvertFiles`, …) holding orchestration from `Base._convert` / `_get_tag_info` and command `__init__`
- Rewrite `commands.py` classes as thin driving adapters: parse args → build request → call use case
- Add composition root in `presentation/cli/` that wires concrete adapters into use cases (constructor injection)
- **Why now**: The use case is the seam between "a human asked for X" and "here's how X happens."

### Phase 6: Retire `Base`, Refocus Tests, Update Docs
- Delete `Base`
- Split tests: domain tests (no mocks), use-case tests (with fake adapters), adapter tests (integration)
- Update `docs/` and `README` to describe the layered architecture
- **Why last**: You only remove the scaffold once the new structure carries the weight.

## Testing Strategy

### Principles
- **Test-first for new domain logic**: Write tests before implementing new domain services and value objects
- **Maintain existing test coverage**: All existing tests must pass after each phase
- **Test at appropriate levels**: Unit tests for domain logic, integration tests for infrastructure, end-to-end tests for workflows
- **Use test doubles**: Mock external dependencies (MusicBrainz API, file system) in domain layer tests

### Test Organization
```
tests/
├── unit/
│   ├── domain/
│   │   ├── catalog/
│   │   │   ├── test_release.py
│   │   │   ├── test_medium.py
│   │   │   └── test_track.py
│   │   ├── audio/
│   │   │   ├── test_converter.py
│   │   │   └── test_tagger.py
│   │   └── acquisition/
│   │       └── test_audio_source.py
│   └── application/
│       └── test_workflow_orchestrator.py
├── integration/
│   ├── infrastructure/
│   │   ├── test_musicbrainz_client.py
│   │   └── test_filesystem_repository.py
│   └── test_end_to_end.py
└── fixtures/
    └── test_data/
```

### Per-Phase Testing Requirements

**Phase 0: Language & Guardrails**
- Run full test suite after creating skeleton
- No new tests required (pure structural change)
- Verify import-linter contract passes

**Phase 1: Purify Domain Model**
- Write unit tests for each new value object before implementation
- Test invariants (e.g., DiscPosition validation)
- Ensure existing tests still pass after moving entities
- Add domain tests for aggregate behavior (Release invariants)

**Phase 2: Declare Ports**
- Write unit tests for port interfaces using test doubles
- Ensure existing tests still pass after moving ABCs
- Add integration tests for accidental ports (AudioSource, etc.)

**Phase 3: Extract Infrastructure**
- Write unit tests for repository interfaces using test doubles
- Write integration tests for filesystem repository implementations
- Write integration tests for MusicBrainz ACL
- Test encoder adapters with real subprocess calls in integration suite

**Phase 4: Extract Presentation**
- Write unit tests for UserInterface port using test doubles
- Write integration tests for ConsoleUI adapter
- Ensure all I/O is behind the port (no print/input in core)

**Phase 5: Use Cases**
- Write unit tests for application services
- Write integration tests for command handlers
- Ensure CLI commands work as before (regression testing)
- Test that orchestration logic is correctly delegated to application services

**Phase 6: Retire Base**
- Split tests into domain/use-case/adapter categories
- Ensure domain tests have no mocks (pure objects)
- Ensure use-case tests use fake adapters
- Ensure adapter tests are integration tests
- Run full regression test suite

### Continuous Testing
- Run `pytest` after each significant change within a phase
- Use `pytest-xdist` for parallel test execution to speed up feedback
- Set up pre-commit hooks to run relevant tests
- Consider adding a CI gate that requires all tests to pass before merging

### Test Data Management
- Keep existing test data in `tests/test_data/`
- Add fixtures for new domain objects as needed
- Use factory pattern (e.g., `factory_boy`) for creating test data
- Ensure test data is isolated and doesn't leak between tests

### Coverage Goals
- Maintain current coverage levels throughout migration
- Target 80%+ coverage for new domain layer code
- Focus coverage on business-critical paths
- Use `pytest-cov` to generate coverage reports

## Consequences

### Positive
- Clearer separation of concerns makes the code easier to understand
- Domain logic is centralized and more testable
- Ports & adapters enable easier testing and swapping of implementations
- Value objects prevent primitive obsession and improve type safety
- Better alignment with business language (ubiquitous language)
- Anti-Corruption Layer prevents external model leakage
- Import-linter makes architecture enforceable
- Incremental migration minimizes risk
- Educational approach teaches DDD concepts through practice

### Negative
- Significant refactoring effort required
- Temporary increase in complexity during migration
- Learning curve for team members unfamiliar with DDD
- More boilerplate code (ports, adapters, etc.)
- Deferred patterns may need to be added later if needs change

### Neutral
- File structure will change significantly
- Some classes may need to be split or merged
- Tests will need to be updated to reflect new structure
- Migration will be done incrementally to minimize disruption
- Single bounded context may need to split if project scales significantly

## Alternatives Considered

1. **Status quo**: Continue with current architecture - rejected due to increasing maintenance burden
2. **Full tactical DDD with multiple contexts** (original Plan A): More complex than needed for this project's scope; multiple bounded contexts create integration overhead without benefit for single-developer project
3. **Clean Architecture**: More complex than needed; hexagonal architecture provides same benefits with simpler terminology
4. **Big bang rewrite**: Too risky; incremental strangler pattern is safer

## Learning Checkpoints

Pause at each phase boundary and answer these to ensure concepts land:

- **After Phase 0**: Why is the dependency rule important? What happens if it's violated?
- **After Phase 1**: Which of my model classes are entities and which are value objects, and why? What invariant does `Release` protect?
- **After Phase 2**: For each port, who "owns" the interface and who "conforms"? Which way do the dependency arrows point?
- **After Phase 3**: What foreign concepts did the MusicBrainz ACL stop from leaking inward?
- **After Phase 4**: Could I run a full "convert" in a unit test with zero real I/O?
- **After Phase 5**: If I had to add a web UI tomorrow, which layers change and which don't?
- **After Phase 6**: Which deferred pattern is the first I'd expect to actually need, and what would trigger it?
