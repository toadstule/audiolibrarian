#  Copyright (c) 2020 Stephen Jibson
#
#  This file is part of audiolibrarian.
#
#  audiolibrarian is free software: you can redistribute it and/or modify it under the terms of the
#  GNU General Public License as published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  audiolibrarian is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
#  without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See
#  the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with audiolibrarian.
#  If not, see <https://www.gnu.org/licenses/>.
#

from unittest import TestCase

from audiolibrarian.records import (
    FrontCover,
    ListF,
    Medium,
    OneTrack,
    People,
    Performer,
    Release,
    Source,
    Track,
)


class TestOneTrack(TestCase):
    one_track = OneTrack(
        release=Release(
            album="Album",
            album_artists=ListF(["Album Artist One", "Album Artist Two"]),
            album_artists_sort=ListF(["One, Album Artist", "Two, Album Artist"]),
            asins=["ASIN 1", "ASIN 2"],
            barcodes=["Barcode 1", "Barcode 2"],
            catalog_numbers=["Catalog Number 1", "Catalog Number 2"],
            date="2015-09-24",
            front_cover=FrontCover(data=b"", desc="front", mime="image/jpg"),
            genres=ListF(["Genre 1", "Genre 2"]),
            labels=["Label 1", "Label 2"],
            media={
                7: Medium(
                    formats=ListF(["Media 1 Format"]),
                    titles=["Disc title 1", "Disc title 2"],
                    track_count=10,
                    tracks={
                        3: Track(
                            artist="Track Artist",
                            artists=ListF(["Track Artist One", "Track Artist Two"]),
                            artists_sort=["One, Track Artist", "Two, Track Artist"],
                            isrcs=["ISRCS 1", "ISRCS 2"],
                            musicbrainz_artist_ids=ListF(["MB-Artist-ID-1", "MB-Artist-ID-2"]),
                            musicbrainz_release_track_id="MB-Release-Track-ID",
                            musicbrainz_track_id="MB-Track_ID",
                            title="Track Title",
                            track_number=3,
                        )
                    },
                )
            },
            medium_count=14,
            musicbrainz_album_artist_ids=ListF(["MB-Album-Artist-ID-1", "MB-Album-Artist-ID-2"]),
            musicbrainz_album_id="MB-Album-ID",
            musicbrainz_release_group_id="MB-Release-Group_ID",
            original_date="1972-04-02",
            original_year="1992",
            people=People(
                engineers=["Engineer 1", "Engineer 2"],
                lyricists=["Lyricist 1", "Lyricist 2"],
                mixers=["Mixer 1", "Mixer 2"],
                performers=[
                    Performer(name="Performer 1", instrument="Instrument 1"),
                    Performer(name="Performer 2", instrument="Instrument 2"),
                ],
                producers=["Producer 1", "Producer 2"],
            ),
            release_countries=["Release Country 1", "Release Country 2"],
            release_statuses=["Release Status 1", "Release Status 2"],
            release_types=["Release Type 1", "Release Type 2"],
            script="Script",
            source=Source.TAGS,
        ),
        medium_number=7,
        track_number=3,
    )

    def test_get_artist_album_disc_path(self):
        self.assertEqual(
            "One,_Album_Artist/1992__Album/disc7", str(self.one_track.get_artist_album_disc_path())
        )
        self.one_track.medium_number = 1
        self.one_track.release.medium_count = 1
        self.assertEqual(
            "One,_Album_Artist/1992__Album", str(self.one_track.get_artist_album_disc_path())
        )
