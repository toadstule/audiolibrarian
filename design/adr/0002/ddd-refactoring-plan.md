# DDD Refactoring Plan (Integrated Approach)

This document outlines the step-by-step plan for refactoring audiolibrarian to adopt Domain-Driven Design principles using a pragmatic hexagonal architecture, as described in ADR 0002. It serves as a working document for planning and tracking the migration effort.

## Overview

The refactoring will be executed incrementally in phases to minimize disruption and allow for continuous testing. Each phase builds on the previous one, with the goal of achieving a clean separation between presentation, application, domain, and infrastructure layers.

**Key Approach Decisions**:
- **Learning-oriented**: Each phase includes "why" explanations to teach DDD concepts
- **Aggressive cleanup**: Old files will be deleted promptly after each phase; git preserves history if needed
- **No backward compatibility concerns**: Small current user base allows breaking changes
- **Test-green phases**: Each phase keeps the test suite green; strangler pattern approach
- **Architecture enforcement**: Import-linter contract makes dependency rule executable
- **Rollback strategy**: Each phase is a separate commit; if a phase gets stuck, use `git reset --hard HEAD~1` to rollback

## Target Architecture

### Domain Layer
Contains pure business logic with no external dependencies.

```
src/audiolibrarian/domain/
├── __init__.py
├── model/
│   ├── __init__.py
│   ├── release.py        # Release (root), Medium, Track            [entities]
│   │                     # Release references Album via album_name/album_id
│   │                     # Medium has media_type (CD, LP, Cassette, Digital) and position
│   ├── values.py         # FrontCover, FileInfo, Performer, People,
│   │                     # DiscPosition, TrackNumber, AudioFormat    [value objects]
│   └── enums.py          # BitrateMode, FileType, Source
└── services/
    ├── __init__.py
    ├── source_matching.py  # match source files → tracks; count invariant
    └── library_layout.py   # artist/album/disc path rules
```

### Application Layer
Orchestrates domain objects to fulfill use cases. Defines ports (interfaces) that the core needs.

```
src/audiolibrarian/application/
├── __init__.py
├── ports/              # interfaces the core needs (abstractions it OWNS)
│   ├── __init__.py
│   ├── metadata_provider.py
│   ├── audio_source.py
│   ├── tag_gateway.py       # read/write tags (today's AudioFile ABC)
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

```
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

**Note**: Each adapter module's `__init__.py` will contain factory functions for creating adapter instances (e.g., `encoders/__init__.py` exports `create_encoders()` that returns all three encoder instances).

### Presentation Layer
CLI-specific code and composition root.

```
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
- **Test-first for new domain logic**: Write tests before implementing new domain services and value objects
- **Maintain existing test coverage**: All existing tests must pass after each phase
- **Test at appropriate levels**: Unit tests for domain logic, integration tests for infrastructure, end-to-end tests for workflows
- **Use test doubles**: Mock external dependencies (MusicBrainz API, file system) in domain layer tests
- **Use pytest-vcr for external API tests**: Record/replay real API responses for MusicBrainz integration tests to avoid rate limiting and network flakiness

### Test Organization
```
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

**Phase 0: Language & Guardrails**
- Run full test suite after creating skeleton
- No new tests required (pure structural change)
- Verify import-linter contract passes
- Update imports in existing tests to reference new locations if needed

**Phase 1: Purify Domain Model**
- Write unit tests for each new value object before implementation
- Test invariants (e.g., DiscPosition validation, TrackNumber formatting)
- Ensure existing tests still pass after moving entities
- Add domain tests for aggregate behavior (Release invariants)
- Test that value objects are immutable (frozen dataclass)

**Phase 2: Declare Ports**
- Write unit tests for port interfaces using test doubles
- Ensure existing tests still pass after moving ABCs
- Add integration tests for accidental ports (AudioSource, Normalizer, TagGateway)
- Test that adapters correctly implement port interfaces

**Phase 3: Extract Infrastructure**
- Write unit tests for repository interfaces using test doubles
- Write integration tests for filesystem repository implementations
- Write integration tests for MusicBrainz ACL using pytest-vcr to record/replay API responses
- Test encoder adapters with real subprocess calls in integration suite
- Test that infrastructure has no dependencies on application/presentation

**Phase 4: Extract Presentation**
- Write unit tests for UserInterface port using test doubles
- Write integration tests for ConsoleUI adapter
- Ensure all I/O is behind the port (no print/input in core)
- Test that prompts and summaries render correctly

**Phase 5: Use Cases**
- Write unit tests for application services
- Write integration tests for command handlers
- Ensure CLI commands work as before (regression testing)
- Test that orchestration logic is correctly delegated to application services
- Test composition root wiring

**Phase 6: Retire Base**
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
- Use direct instantiation with attrs classes for test data (e.g., `Release(album="Dark Side", ...)`)
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
- Create the empty `domain/ application/ infrastructure/ presentation/` skeleton with `__init__.py` files
- Add import-linter contract enforcing the dependency rule:
  - Install `import-linter` package
  - Create `.importlinter` configuration file with contract:
    ```
    [[contracts]]
    name = "domain-layer-dependency-rule"
    type = "layers"
    layers = ["domain", "application", "infrastructure", "presentation"]
    containers = [
        "audiolibrarian.domain",
        "audiolibrarian.application",
        "audiolibrarian.infrastructure",
        "audiolibrarian.presentation",
    ]
    ```
  - This ensures: domain imports nothing, application imports only domain, infrastructure imports only application+domain, presentation imports only application+domain+infrastructure
- Configure import-linter in pyproject.toml:
  - Add to dev dependencies
  - Add pre-commit hook or CI check
- Add pytest-vcr to dev dependencies in pyproject.toml for MusicBrainz API testing
- Run full test suite to ensure skeleton doesn't break anything

**Why first**: The language and the dependency rule are the two things that, once agreed, make every later decision obvious. The linter makes the architecture executable - violations fail CI instead of rotting silently.

**DDD concept taught**: Ubiquitous Language, the Dependency Rule

**Learning checkpoint**: Why is the dependency rule important? What happens if it's violated?

---

### Phase 1: Purify the Domain Model

**Tasks**:
- Move `records.py` into `domain/model/` split into:
  - `release.py` - Release, Medium, Track entities (Release references Album via album_name/album_id)
  - `values.py` - FrontCover, FileInfo, Performer, People value objects
  - `enums.py` - BitrateMode, FileType, Source enums
- Freeze value objects with `@attr.frozen=True` (attrs is already a project dependency)
- Introduce new value objects to cure primitive obsession:
  - `DiscPosition(number, count)` - validates `1 ≤ number ≤ count` once
  - `TrackNumber(int)` - knows how to render as `"02"` and parse from filename
  - `AudioFormat` - FLAC/M4A/MP3 as first-class concept
- Keep existing behavior methods (`get_filename`, path helpers)
- Move path helpers to `domain/services/library_layout.py`:
  - Criterion: If a helper encodes business rules about library structure (e.g., "artist/album/disc" layout), it's domain
  - If a helper uses `os.path` only for path joining (no business logic), it can stay in domain/services
  - If a helper interacts with the actual filesystem (checking if paths exist), it's infrastructure
- Ensure `domain/` imports only stdlib + external libraries + itself (no cross-layer imports)
- Update imports throughout codebase:
  - Search for imports of `records` module (e.g., `from audiolibrarian import records`)
  - Replace with new imports (e.g., `from audiolibrarian.domain.model import release`)
  - Update test files: search for `records` imports in `tests/` and update to new locations
- Run full test suite

**Why now**: The domain is the center of the hexagon; everything else will depend on it, so it must be clean and dependency-free before we build outward.

**DDD concept taught**: Entity vs. Value Object, Aggregate & invariants, curing primitive obsession

**Learning checkpoint**: Which of my model classes are entities and which are value objects, and why? What invariant does `Release` protect?

---

### Phase 2: Declare the Ports; Reclassify Existing ABCs as Adapters

**Tasks**:
- Create the `application/ports/*` interfaces:
  - `metadata_provider.py` - MetadataProvider port
  - `audio_source.py` - AudioSource port (today's ABC becomes the interface)
  - `tag_gateway.py` - TagGateway port (today's AudioFile ABC)
  - `encoder.py` - Encoder port
  - `normalizer.py` - Normalizer port (today's ABC)
  - `library_repository.py` - LibraryRepository port
  - `user_interface.py` - UserInterface port
- Move existing ABCs to become the port interfaces
- Move concrete implementations to `infrastructure/` as adapters:
  - `CDAudioSource`, `FilesAudioSource` → `infrastructure/audiosources/`
  - `AudioFile` subclasses → `infrastructure/tags/`
  - `Normalizer` subclasses → `infrastructure/normalizers/`
- Update imports throughout codebase:
  - Search for imports of moved ABCs (e.g., `from audiolibrarian.audiofile import AudioFile`)
  - Replace with port imports (e.g., `from audiolibrarian.application.ports.tag_gateway import TagGateway`)
  - Update `Base` and command classes to use new import locations
- Run full test suite

**Why now**: With a clean domain, we can express what the core needs as interfaces before touching the tangled `Base`.

**DDD concept taught**: Ports & Adapters, Dependency Inversion

**Learning checkpoint**: For each port, who "owns" the interface and who "conforms"? Which way do the dependency arrows point, and why is that inverted from a naive design?

---

### Phase 3: Extract Infrastructure out of `Base`

**Tasks**:
- Pull `_make_flac`, `_make_m4a`, `_make_mp3` from `Base` into `Encoder` adapters:
  - Create `infrastructure/encoders/flac_encoder.py`
  - Create `infrastructure/encoders/m4a_encoder.py`
  - Create `infrastructure/encoders/mp3_encoder.py`
- Pull `_move_files`, `get_artist_album_path`, `_write_manifest`, `_read_manifest` from `Base` into `FilesystemLibraryRepository`:
  - Create `infrastructure/library/filesystem_library_repository.py`
- Wrap `musicbrainz.py` as the `MusicBrainzProvider` ACL behind `MetadataProvider`:
  - Create `infrastructure/musicbrainz/musicbrainz_provider.py`
  - Create `infrastructure/musicbrainz/musicbrainz_mapper.py`
  - Use Pydantic for DTOs at the MusicBrainz API boundary (validation/serialization)
- Update `Base` to use the new adapters
- Run full test suite

**Why now**: `Base` shrinks to pure orchestration once the "how" (infrastructure) is gone.

**DDD concept taught**: Repository, Anti-Corruption Layer

**Learning checkpoint**: What foreign concepts did the MusicBrainz ACL stop from leaking inward? Name three.

---

### Phase 4: Extract Presentation

**Tasks**:
- Introduce `UserInterface` port in `application/ports/user_interface.py` with methods:
  - `confirm(summary) -> bool`
  - `prompt(message) -> str`
  - `show(message)`
  - `display_table(data)`
- Create `ConsoleUI` adapter in `presentation/console_ui.py`:
  - Implements UserInterface using print, text.input_, and table rendering
- Move `_summary` rendering from `Base` to `ConsoleUI`
- Move all `print`, `text.input_`, and confirm logic from `Base` to `ConsoleUI`
- Move prompts currently inside `musicbrainz.py` (e.g., "Genre not found") to use UserInterface
- Update `Base` to use UserInterface port
- Run full test suite

**Why now**: With I/O gone, the remaining `Base` logic is pure decisions (application orchestration).

**DDD concept taught**: Keeping I/O at the edges; testability of a pure core

**Learning checkpoint**: Could I run a full "convert" in a unit test with zero real I/O? If not, what's still leaking?

---

### Phase 5: Introduce Use Cases; Make Commands Thin

**Approach Migrate one use case/command at a time to maintain test-green status. Each sub-phase converts one command to the new architecture.**

**Phase 5a: RipAlbum use case**
- Create `application/use_cases/rip_album.py` with RipAlbum use case
- Move orchestration logic from `Rip.__init__` and `Base._convert`/`_get_tag_info` into use case
- Create request DTO as attrs class: `RipRequest(search_data, disc_position)`
- Rewrite `Rip` command as thin adapter using tyro
- Add factory functions to relevant adapter `__init__.py` files
- Add composition root function for RipAlbum in `presentation/cli/composition_root.py`
- Update CLI entry point to use new Rip command
- Run tests for rip command
- Commit: "refactor(app): add RipAlbum use case; convert Rip command to tyro"

**Phase 5b: ConvertFiles use case**
- Create `application/use_cases/convert_files.py` with ConvertFiles use case
- Move orchestration logic from `Convert.__init__` and `Base._convert`/`_get_tag_info` into use case
- Create request DTO as attrs class: `ConvertRequest(filenames, search_data, disc_position)`
- Rewrite `Convert` command as thin adapter using tyro
- Add composition root function for ConvertFiles
- Update CLI entry point
- Run tests for convert command
- Commit: "refactor(app): add ConvertFiles use case; convert Convert command to tyro"

**Phase 5c: Remaining use cases**
- Repeat pattern for: Reconvert, Rename, Manifest, Genre
- One use case per sub-phase
- Each sub-phase: create use case, rewrite command, add composition root, test, commit

**Phase 5d: Cleanup**
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
  - `infrastructure/encoders/__init__.py`: `create_encoders()` returns tuple of (FlacEncoder, M4aEncoder, Mp3Encoder)
  - `infrastructure/tags/__init__.py`: `TagGateway()` auto-detects format from file extension
  - `infrastructure/normalizers/__init__.py`: `create_normalizer(settings)` wraps existing factory pattern
  - `infrastructure/audiosources/__init__.py`: `create_audio_source()` based on command type

**Why now**: The use case is the seam between "a human asked for X" and "here's how X happens." Thin commands mean the CLI is just one trigger among possible many.

**DDD concept taught**: Application Service / Use Case, Composition Root, dependency injection

**Learning checkpoint**: If I had to add a web UI tomorrow, which layers change and which don't?

---

### Phase 6: Retire `Base`, Refocus Tests, Update Docs

**Tasks**:
- Delete `Base` class
- Delete `base.py` file
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

**Learning checkpoint**: Which deferred pattern (from ADR 0002) is the first I'd expect to actually need, and what would trigger it?

---

## Suggested Commit Sequence

```
chore(ddd): add glossary + layer skeleton + import-linter contract    (Phase 0)
refactor(domain): extract pure domain model + value objects           (Phase 1)
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

The following patterns are deliberately deferred until the pain they solve is actually felt:

| Pattern                         | Why Deferred                                                                           | Adopt When…                                                                             |
|---------------------------------|----------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------|
| **Domain Events**               | No subscribers exist; nothing reacts asynchronously. Pure ceremony.                    | You add side effects (notify, index, sync) that shouldn't be hard-wired into use cases. |
| **Factories as objects**        | The ACL already is the construction logic; a separate class adds indirection.          | Construction rules get complex enough to reuse/test independently.                      |
| **Formal Domain Services**      | Plain functions in `domain/services/` are enough and simpler.                          | Logic grows state or multiple collaborating strategies.                                 |
| **Unit of Work / transactions** | Filesystem work-dir + move already gives crude atomicity; single user, no concurrency. | Partial-failure corruption becomes a real problem.                                      |
| **Specification pattern**       | One fuzzy-match rule; a helper function suffices.                                      | Matching rules multiply and need to combine.                                            |
| **CQRS**                        | The app is essentially all "commands" already; no read-scaling need.                   | Query needs diverge sharply from write needs.                                           |
| **Multiple Bounded Contexts**   | One language, one dev - no linguistic strain.                                          | Language conflicts or team boundaries emerge.                                           |

## Success Criteria

The refactoring is complete when:
- [ ] All 6 phases are completed
- [ ] `Base` class is removed
- [ ] All tests pass with new structure
- [ ] Import-linter contract passes
- [ ] Domain layer has no external dependencies
- [ ] All I/O is behind ports
- [ ] CLI commands are thin adapters
- [ ] Documentation is updated
- [ ] Learning checkpoints are answered
