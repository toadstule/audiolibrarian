# Getting Started

This guide will help you get up and running with audiolibrarian.

## Directory Structure

`audiolibrarian` organizes files in the following structure:

**Processed audio files** (organized by format):

```text
library/
├── flac/
│   └── Artist/
│       └── YYYY__Album/
│           ├── 01__Track_Title.flac
│           └── 02__Another_Track.flac
├── m4a/
│   └── Artist/
│       └── YYYY__Album/
│           ├── 01__Track_Title.m4a
│           └── 02__Another_Track.m4a
├── mp3/
│   └── Artist/
│       └── YYYY__Album/
│           ├── 01__Track_Title.mp3
│           └── 02__Another_Track.mp3
└── source/
    └── Artist/
        └── YYYY__Album/
            ├── 01__Track_Title.flac
            ├── 02__Another_Track.flac
            └── Manifest.yaml
```

> NOTE: the `source` directory is explained in
> [The Source Directory](./advanced.md#the-source-directory) section of
> [Advanced Topics](./advanced.md).

## Basic Commands

### View Help

```bash
audiolibrarian --help
```

### Add Audio from a CD

```bash
audiolibrarian rip
```

This will:

1. Read the CD
2. Look up metadata on MusicBrainz
3. Show a preview of the rip
4. Prompt for confirmation
5. Rip the CD and add audio to your library

**Sample output:**

```text
$ audiolibrarian rip

Gathering search information...
Finding MusicBrainz release information...
╔══════════════════════════════════════════════════════════════════════════════════╗
║ Album:      I-Empire                                                             ║
║ Artist(s):  Angels & Airwaves                                                    ║
║ MB Release: https://musicbrainz.org/release/374cb6ec-8d62-456f-aa9b-55fb4f85d22d ║
║ Disc:       1 of 1                                                               ║
╠══════════════╤═══════════════════════╤═══════════════════════════════════════════╣
║ Source       │ Destination           │ Title                                     ║
╠══════════════╪═══════════════════════╪═══════════════════════════════════════════╣
║ track01.cdda │ 01__Call_to_Arms      │ 01: Call to Arms                          ║
║ track02.cdda │ 02__Everythings_Magic │ 02: Everything's Magic                    ║
║ track03.cdda │ 03__Breathe           │ 03: Breathe                               ║
║ track04.cdda │ 04__Love_Like_Rockets │ 04: Love Like Rockets                     ║
║ track05.cdda │ 05__Sirens            │ 05: Sirens                                ║
║ track06.cdda │ 06__Secret_Crowds     │ 06: Secret Crowds                         ║
║ track07.cdda │ 07__Star_of_Bethlehem │ 07: Star of Bethlehem                     ║
║ track08.cdda │ 08__True_Love         │ 08: True Love                             ║
║ track09.cdda │ 09__Lifeline          │ 09: Lifeline                              ║
║ track10.cdda │ 10__Jumping_Rooftops  │ 10: Jumping Rooftops                      ║
║ track11.cdda │ 11__Rite_of_Spring    │ 11: Rite of Spring                        ║
║ track12.cdda │ 12__Heaven            │ 12: Heaven                                ║
╚══════════════╧═══════════════════════╧═══════════════════════════════════════════╝
Confirm [N,y]: y

Making 12 flac files...............
Normalizing wav files...
Making 12 flac files...............
Making 12 m4a files...............
Making 12 mp3 files...............
Wrote /home/user/library/source/Angels_and_Airwaves/2007__I-Empire/Manifest.yaml
```

### Add Audio from Files

```bash
audiolibrarian convert /path/to/audio/files
```

This will:

1. Prompt you for a MusicBrainz release ID (UUID or URL)
2. Preview the source and destination names
3. Prompt for confirmation
4. Convert the audio and add it to your library

**Sample output:**

```text
$ ls APP__VULTURE_CULTURE
'1-lets talk about me.flac'  '4-sooner or later.flac'  '7-somebody out there.flac'
'2-separate lives.flac'      '5-vulture culture.flac'  '8-same old sun.flac'
'3-days are numbers.flac'     6-hawkeye.flac


$ audiolibrarian convert APP__VULTURE_CULTURE
Gathering search information...
Finding MusicBrainz release information...
MusicBrainz Release ID: https://musicbrainz.org/release/415f07fb-47de-3d4e-bbf9-683791188b75
╔═══════════════════════════════════════════════════════════════════════════════════════════════════╗
║ Album:      Vulture Culture                                                                       ║
║ Artist(s):  Parsons, Alan, Project, The                                                           ║
║ MB Release: https://musicbrainz.org/release/415f07fb-47de-3d4e-bbf9-683791188b75                  ║
║ Disc:       1 of 1                                                                                ║
╠══════════════════════╤═════════════════════════════════════╤══════════════════════════════════════╣
║ Source               │ Destination                         │ Title                                ║
╠══════════════════════╪═════════════════════════════════════╪══════════════════════════════════════╣
║ 1-lets talk about me │ 01__Lets_Talk_About_Me              │ 01: Let's Talk About Me              ║
║ 2-separate lives     │ 02__Separate_Lives                  │ 02: Separate Lives                   ║
║ 3-days are numbers   │ 03__Days_Are_Numbers__The_Traveller │ 03: Days Are Numbers (The Traveller) ║
║ 4-sooner or later    │ 04__Sooner_or_Later                 │ 04: Sooner or Later                  ║
║ 5-vulture culture    │ 05__Vulture_Culture                 │ 05: Vulture Culture                  ║
║ 6-hawkeye            │ 06__Hawkeye                         │ 06: Hawkeye                          ║
║ 7-somebody out there │ 07__Somebody_Out_There              │ 07: Somebody Out There               ║
║ 8-same old sun       │ 08__The_Same_Old_Sun                │ 08: The Same Old Sun                 ║
╚══════════════════════╧═════════════════════════════════════╧══════════════════════════════════════╝
Confirm [N,y]: y
Making 8 wav files...........
Making 8 flac files...........
Normalizing wav files...
Making 8 flac files...........
Making 8 m4a files...........
Making 8 mp3 files...........
Wrote /home/user/library/source/Parsons,_Alan,_Project,_The/1985__Vulture_Culture/Manifest.yaml
```
