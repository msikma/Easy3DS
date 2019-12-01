#!/usr/bin/env bash

# Abort on error
set -e

# Get the project's root directory, possibly through a symlink. <https://stackoverflow.com/a/246128>
BASE="$( cd "$( dirname "${BASH_SOURCE[0]}" )" > /dev/null 2>&1 && pwd )"

PROJECT="easy3ds"
SELF="easy3ds.sh"
VERSION="1.0.0"
HOMEPAGE="https://github.com/msikma/easy3ds"

# Global settings used in make_cia().
dir_assets="$BASE/assets"
dir_tmp="$BASE/tmp"
dir_output="$BASE/out"
path_easyrpg_bin="$BASE/assets/easyrpg-player.elf"

# Checks whether the required tools are installed.
function check_prerequisites {
  arr=('bannertool' '3dstool' 'makerom')
  for tool in "${arr[@]}"; do
    if ! command -v $tool >/dev/null 2>&1; then
      echo "$SELF: error: the '$tool' command is not available (see readme for a list of prerequisites)"
      exit
    fi
  done
}

# Retrieves the value of a specific key from a game's gameinfo.cfg file.
function game_info {
  cat "$1/3DS/gameinfo.cfg" | sed -n "s/$2[ ]*=[ ]*\(.*\)$/\1/p"
}

# Generates a single CIA file for a game directory.
function make_cia {
  local dir_game="$1"

  local slug=$(basename "$dir_game")
  local unique_id=$(game_info "$dir_game" "cia_id")
  local title=$(game_info "$dir_game" "title")
  local author=$(game_info "$dir_game" "author")
  local release=$(game_info "$dir_game" "release")

  local dir_assets_game="$dir_game/3DS"
  local dir_romfs="$dir_game"
  local cia_output="$dir_output/$slug.cia"

  if [ "$unique_id" = "000000" ]; then
    echo "Skipping game: \"$slug\": set a unique ID"
    return
  fi
  if [ -z "$title" ] || [ -z "$author" ] || [ -z "$unique_id" ]; then
    echo "Skipping game: \"$slug\": gameinfo.cfg file is incomplete (see readme)"
    return
  fi

  echo "Building game: \"$slug\" (title=\"$title\", author=\"$author\", release=\"$release\", id=\"$unique_id\")"
  
  mkdir -p "$dir_tmp"
  bannertool makebanner -i "$dir_assets_game/banner.png" -a "$dir_assets_game/audio.wav" -o "$dir_tmp/banner.bin" > /dev/null
  bannertool makesmdh -s "$title" -l "$title" -p "$author" -i "$dir_assets_game/icon.png" -o "$dir_tmp/icon.bin" > /dev/null
  3dstool -ctf romfs "$dir_tmp/romfs.bin" --romfs-dir "$dir_romfs"
  cat "$dir_assets/spec.rsf" | sed "s/{{UNIQUE_ID}}/$unique_id/" > "$dir_tmp/spec.rsf"
  makerom -f cia -o "$cia_output" -elf "$path_easyrpg_bin" -rsf "$dir_tmp/spec.rsf" -icon "$dir_tmp/icon.bin" -banner "$dir_tmp/banner.bin" -exefslogo -target t -romfs "$dir_tmp/romfs.bin"

  echo "Output: $cia_output"
}

# CLI interface. Parses arguments, shows help usage, and runs the main program.
function argparse {
  usage="usage: $SELF [-h] [-v] {cia,cia-dir} dir"
  case $1 in
    cia)
      if [ -z "$2" ]; then
        cat << EOF
$usage
$SELF: error: the cia command must be followed by one directory argument
EOF
        exit 1
      fi
      check_prerequisites
      make_cia "$2"
      ;;
    cia-dir)
      if [ -z "$2" ]; then
        cat << EOF
$usage
$SELF: error: the cia-dir command must be followed by one directory argument
EOF
        exit 1
      fi
      check_prerequisites
      for dir in "$2/"*; do
        make_cia "$dir"
      done
      ;;
    -v|--version)
      echo "$PROJECT-$VERSION"
      ;;
    *)
      if [[ $1 == "-h" || $1 == '--help' ]]; then
        cat << EOF
$usage

Script for converting RPG Maker 2000/2003 games into 3DS games using the
EasyRPG player. EasyRPG is an open source recreation of the RPG Maker engine,
making it possible to play RPG Maker games on all modern operating systems
and consoles - among them the 3DS.

For converting a single game to .CIA, use the 'cia' command:

  $ ./build.sh cia ./my-rm2k-game

The 'my-rm2k-game' dir must contain the game itself (e.g. the RPG_RT.ini file)
and a '3DS' subdir containing the necessary assets for CIA file generation.
See the readme file for details on creating these.

Commands:
  cia                   Generates a .CIA file for a single game
  cia-dir               Iterates over subdirs and generates multiple .CIA files

Optional arguments:
  -h, --help            Show this help message and exit.
  -v, --version         Show program's version number and exit.

For more information, see <$HOMEPAGE>.
EOF
        exit 0
      fi
      if [ -z "$1" ]; then
        cat << EOF
$usage
$SELF: error: too few arguments
EOF
        exit 1
      fi
      if [ ! -z "$1" ]; then
        cat << EOF
$usage
$SELF: error: Invalid command: $1 (choose from [cia, cia-dir])
EOF
        exit 1
      fi
      ;;
  esac
}

# Parse CLI arguments if the script is being run standalone.
if [[ "${BASH_SOURCE[0]}" = "${0}" ]]; then
  argparse $@
fi
