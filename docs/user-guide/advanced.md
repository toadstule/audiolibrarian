# Advanced Topics

## The Source Directory

The `source` directory contains a lossless copy of the original source files, with no
normalization. The source files are tagged with MusicBrainz tags to make re-converting them
easier.

For example, if you're not happy with the normalization level performed by `audiolibrarian`,
you can update the normalization settings, then re-convert all the files in your library by
running `audiolibrarian reconvert` on the `source` directory.

When backing up your library, you may choose to only back up the `source` directory. The rest
of your files can be re-generated from the `source` directory using `audiolibrarian reconvert`,
after you've restored from your backup.
