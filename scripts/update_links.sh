#!/bin/bash
#
#  Copyright (c) 2000-2025 Stephen Jibson
#
#  This file is part of audiolibrarian.
#
#  Audiolibrarian is free software: you can redistribute it and/or modify it under the terms of the
#  GNU General Public License as published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  Audiolibrarian is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
#  without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See
#  the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with audiolibrarian.
#  If not, see <https://www.gnu.org/licenses/>.
#

# This file should be located in the /bin directory of the library (i.e. "/media/music/bin")
# along side the flac, m4a, mp3 directories

#set -x
music_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )"/../ >/dev/null 2>&1 && pwd )"

function make_links {
  dst=$1
  src=$2
  pushd "$dst" > /dev/null || exit 1
  find . -type l -exec rm -f {} \;
  for d in ../"$src"/*; do
    base=$(basename "$d")
    if [[ -d "../$src/$d" ]]; then
      if [[ ! -d "$base" ]]; then
        mkdir "$base"
      fi
    fi
    for source in "$d"/*; do
#    echo "$source"
      ln -sf ../"$source" "$base"/
    done
  done
  popd  > /dev/null || exit 1
}

pushd "$music_dir" > /dev/null || exit 1

make_links best mp3
make_links best m4a
make_links best flac
make_links ios mp3
make_links ios m4a

popd > /dev/null || exit 1
