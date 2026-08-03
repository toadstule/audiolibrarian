#  Copyright (C) 2020-2025 Stephen T. Jibson.
#  SPDX-License-Identifier: GPL-3.0-only

"""Test records."""

import pytest

from audiolibrarian.domain.model import enums, medium, record, release, track, values


class TestOneTrack:
    """Test one track."""

    @pytest.fixture(scope="class")
    @classmethod
    def one_track(cls) -> release.OneTrack:
        """Return a populated OneTrack instance."""
        return release.OneTrack(
            release=release.Release(
                album="Album",
                album_artists=record.ListF(["Album Artist One", "Album Artist Two"]),
                album_artists_sort=record.ListF(["One, Album Artist", "Two, Album Artist"]),
                asins=["ASIN 1", "ASIN 2"],
                barcodes=["Barcode 1", "Barcode 2"],
                catalog_numbers=["Catalog Number 1", "Catalog Number 2"],
                date="2015-09-24",
                front_cover=values.FrontCover(data=b"", desc="front", mime="image/jpg"),
                genres=record.ListF(["Genre 1", "Genre 2"]),
                labels=["Label 1", "Label 2"],
                media={
                    7: medium.Medium(
                        formats=record.ListF(["Media 1 Format"]),
                        titles=["Disc title 1", "Disc title 2"],
                        track_count=10,
                        tracks={
                            values.TrackNumber(3): track.Track(
                                artist="Track Artist",
                                artists=record.ListF(["Track Artist One", "Track Artist Two"]),
                                artists_sort=["One, Track Artist", "Two, Track Artist"],
                                isrcs=["ISRCS 1", "ISRCS 2"],
                                musicbrainz_artist_ids=record.ListF(["MB-Artist-ID-1", "MB-Artist-ID-2"]),
                                musicbrainz_release_track_id="MB-Release-Track-ID",
                                musicbrainz_track_id="MB-Track_ID",
                                title="Track Title",
                                track_number=values.TrackNumber(3),
                            )
                        },
                    )
                },
                medium_count=14,
                musicbrainz_album_artist_ids=record.ListF(["MB-Album-Artist-ID-1", "MB-Album-Artist-ID-2"]),
                musicbrainz_album_id="MB-Album-ID",
                musicbrainz_release_group_id="MB-Release-Group_ID",
                original_date="1972-04-02",
                original_year="1992",
                people=values.People(
                    engineers=["Engineer 1", "Engineer 2"],
                    lyricists=["Lyricist 1", "Lyricist 2"],
                    mixers=["Mixer 1", "Mixer 2"],
                    performers=[
                        values.Performer(name="Performer 1", instrument="Instrument 1"),
                        values.Performer(name="Performer 2", instrument="Instrument 2"),
                    ],
                    producers=["Producer 1", "Producer 2"],
                ),
                release_countries=["Release Country 1", "Release Country 2"],
                release_statuses=["Release Status 1", "Release Status 2"],
                release_types=["Release Type 1", "Release Type 2"],
                script="Script",
                source=enums.Source.TAGS,
            ),
            medium_position=values.MediumPosition(number=7, count=14),
            track_number=values.TrackNumber(3),
        )
