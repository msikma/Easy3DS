#!/usr/bin/env python3

import argparse
import configparser
import os
import re
import subprocess
import sys
import unicodedata
import zlib
from distutils.spawn import find_executable
from glob import glob


def make_cia_file(id, title, author, release_date, game_path, name, safe_name, banner, audio, icon, elf, spec, tmp, out):
  '''
  Actually builds the CIA file. This procedure creates temporary files that aren't cleaned up here.
  '''
  success = True

  result = subprocess.run(['bannertool', 'makebanner', '-i', banner, '-a', audio, '-o', tmp + '/banner.bin'], capture_output=True)
  if result.returncode != 0: return False
  result = subprocess.run(['bannertool', 'makesmdh', '-s', title, '-l', title, '-p', author, '-i', icon, '-o', tmp + '/icon.bin'], capture_output=True)
  if result.returncode != 0: return False
  result = subprocess.run(['3dstool', '-cvtf', 'romfs', tmp + '/romfs.bin', '--romfs-dir', game_path], capture_output=True)
  if result.returncode != 0: return False
  with open(tmp + '/spec.rsf', 'w') as fp:
    result = subprocess.run(['gsed', '-r', r's/(UniqueId\s+:)\s*.*$/\1 0x$unique_id/g', spec], stdout=fp)
  if result.returncode != 0: return False
  result = subprocess.run(['makerom', '-f', 'cia', '-o', out + '/' + safe_name + '.cia', '-elf', elf, '-rsf', tmp + '/spec.rsf', '-icon', tmp + '/icon.bin', '-banner', tmp + '/banner.bin', '-exefslogo', '-target', 't', '-romfs', tmp + '/romfs.bin'], capture_output=True)
  if result.returncode != 0: return False
  
  return {
    'success': success,
    'id': id,
    'safe_name': safe_name,
    'title': title,
    'author': author,
    'release_date': release_date,
    'name': name
  }


def clean_up_tmp_files(tmp_dir):
  '''
  Removes any temporary files that may have been created while making a CIA file.
  '''
  files = glob(tmp_dir + '/*')
  for file in files:
    os.remove(file)


def build_cia(base, game_path, game_name, elf_path, rtp_dir, spec_path, out_dir, tmp_dir, default_crcs, game_dir=None):
  '''
  Prepares to build a CIA file by assembling all the information needed.
  '''
  assets_path = '{}/3DS/'.format(game_path)
  safe_name = slugify(game_name)
  target = '{}/{}.cia'.format(out_dir, safe_name)
  rel_path = rel_dir(game_path, game_dir)
  rel_target = rel_dir(target, out_dir)

  info = get_config(assets_path + 'info.cfg')['metadata']

  # Check whether this game is using any of the default assets.
  # This raises a warning; if a default info.cfg is found, we fail the build.
  crcs = {
    'audio': crc(assets_path + 'audio.wav'),
    'banner': crc(assets_path + 'banner.png'),
    'icon': crc(assets_path + 'icon.png'),
    'info': crc(assets_path + 'info.cfg')
  }

  game = None
  success = True

  default_items = [item for item in crcs.keys() if crcs[item] == default_crcs[item]]
  if len(default_items) > 1:
    report_default_assets(game_path, game_dir, default_items)
  if 'info' in default_items:
    success = False
  
  if success:
    try:
      game = make_cia_file(
        info['cia_id'],
        info['title'],
        info['author'],
        info.get('release'),
        game_path,
        game_name,
        safe_name,
        assets_path + 'banner.png',
        assets_path + 'audio.wav',
        assets_path + 'icon.png',
        elf_path,
        spec_path,
        tmp_dir,
        out_dir
      )
      success = game['success']
    except:
      success = False
    finally:
      clean_up_tmp_files(tmp_dir)

  return {
    'success': success,
    'dir': rel_path,
    'target': rel_target,
    'game': game
  }


def main():
  '''
  Script main entry point. Parses command-line arguments.
  '''
  parser = argparse.ArgumentParser(description='Script for generating 3DS CIA files from RPG Maker 2000 games using EasyRPG. See readme.md for setting up the build requirements. Only the source directory needs to be specified; defaults will be used for everything else.')

  parser.add_argument('dir', type=str, help='source directory containing an RM2K(3) game, or multiple games')
  parser.add_argument('--elf', type=str, help='path to an EasyRPG ELF file', default='./assets/easyrpg-player.elf')
  parser.add_argument('--spec', type=str, help='path to a ROM spec file (will have a new unique ID inserted)', default='./assets/spec.rsf')
  #parser.add_argument('--rtp', type=str, help='path to an RTP', default='./assets/rtp')
  parser.add_argument('--out', type=str, help='CIA file output directory', default='./out')
  args = parser.parse_args()
  base = os.path.abspath(os.path.dirname(sys.argv[0]))
  tmp_dir = base + '/tmp'

  check_rsf_template(args.spec)
  check_prerequisites()
  check_easyrpg_elf(args.elf)

  build_dir(base, args.dir, args.elf, None, args.spec, args.out, tmp_dir)
  sys.exit(0)


def build(base, item, game_dir, elf_path, rtp_dir, spec_path, out_dir, tmp_dir, report_dir=False):
  '''
  Builds a single game.
  '''
  game_path = '{}/{}'.format(game_dir, item)

  # Calculate CRCs for our default assets, so we can point out when
  # a game is using them (every game should have a unique icon!)
  # Using the default info is an error that fails a build.
  default_base = base + '/assets/defaults/'
  defaults = {
    'audio': crc(default_base + 'audio.wav'),
    'banner': crc(default_base + 'banner.png'),
    'icon': crc(default_base + 'icon.png'),
    'info': crc(default_base + 'info.cfg')
  }

  if not os.path.isdir(game_path):
    if report_dir:
      report_not_a_dir(game_path, game_dir)
    return
  if not is_game(game_path):
    report_not_a_game(game_path, game_dir)
    return
  if not check_3ds_assets(game_path, game_dir):
    return
  if not check_3ds_info(game_path, game_dir):
    return
  result = build_cia(base, game_path, item, elf_path, rtp_dir, spec_path, out_dir, tmp_dir, defaults, game_dir)
  if not result['success']:
    report_build_failed(game_path, game_dir)
  else:
    report_build_succeeded(result)
  return result

def build_dir(base, game_dir, elf_path, rtp_dir, spec_path, out_dir, tmp_dir):
  '''
  Builds either a single game or multiple games.
  '''
  # Check if we're building one game or multiple games.
  if is_game(game_dir):
    bits = os.path.split(game_dir)
    item = bits[1]
    result = build(base, item, game_dir, elf_path, rtp_dir, spec_path, out_dir, tmp_dir, True)
    if result and result['success']:
      return
    else:
      sys.exit(1)
  
  count = 0
  for item in os.listdir(game_dir):
    result = build(base, item, game_dir, elf_path, rtp_dir, spec_path, out_dir, tmp_dir, False)
    if result and result['success']:
      count += 1
  
  report_builds_done(count)


def is_game(dir):
  '''Checks if a directory contains an RPG Maker 2000/2003 game.'''
  return os.path.isfile('{}/RPG_RT.ini'.format(dir)) or os.path.isfile('{}/rpg_rt.ini'.format(dir))


def slugify(value):
  '''Returns a simplified string used for filenames. Taken from the Django codebase.'''
  value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
  value = re.sub(r'[^\w\s-]', '', value).strip()
  return re.sub(r'[-\s]+', '-', value)


def rel_dir(target, base):
  '''Returns a relative link between path A and B, if B is specified; absolute path A otherwise.'''
  if not base:
    return target
  bits = os.path.split(base)
  return '{}/{}'.format(bits[1], os.path.relpath(target, base))


def get_config(path):
  '''Reads a game's config file.'''
  c = configparser.RawConfigParser()
  c.read(path)
  return c


def check_3ds_assets(dir, game_dir):
  '''Checks if a game directory has all the required 3DS assets for making a CIA file. Warns otherwise.'''
  base = '{}/3DS/'.format(dir)
  audio = os.path.isfile(base + 'audio.wav')
  banner = os.path.isfile(base + 'banner.png')
  icon = os.path.isfile(base + 'icon.png')
  info = os.path.isfile(base + 'info.cfg')
  if not (audio and banner and icon and info):
    report_no_assets(dir, game_dir, audio, banner, icon, info)
    return False
  return True


def check_3ds_info(dir, game_dir):
  '''Checks if a game's info.cfg file contains all required information. Warns otherwise.'''
  c = get_config('{}/3DS/info.cfg'.format(dir))
  id = c['metadata']['cia_id']
  title = c['metadata']['title']
  author = c['metadata']['author']

  valid_id = True

  # Check if the ID is valid hexadecimal.
  try:
    int(id, 16)
  except ValueError:
    valid_id = False

  valid_id_length = len(id) == 6
  valid_title = bool(title)
  valid_author = bool(author)

  if not (valid_id_length and valid_id and valid_title and valid_author):
    report_no_info(dir, game_dir, valid_id_length, valid_id, valid_title, valid_author)
    return False
  
  return True


def check_rsf_template(spec_file):
  if not os.path.isfile(spec_file):
    _report_error('could not find ROM spec file: {}'.format(spec_file))
  return False


def check_easyrpg_elf(elf_file):
  if not os.path.isfile(elf_file):
    _report_error('could not find EasyRPG ELF file: {}'.format(elf_file))
  return False


def check_prerequisites():
  has_bannertool = bin_is_available('bannertool')
  has_3dstool = bin_is_available('3dstool')
  has_sed = bin_is_available('sed')
  has_makerom = bin_is_available('makerom')

  if not (has_bannertool and has_3dstool and has_sed and has_makerom):
    report_missing_prerequisites(has_bannertool, has_3dstool, has_sed, has_makerom)
    # Script has already exited here.
    return False
  return True

def bin_is_available(name):
  '''Checks whether a specific executable file is on the path.'''
  return find_executable(name) is not None


def crc(file):
  '''
  Calculates the CRC32 value of a file.
  '''
  prev = 0
  for line in open(file, 'rb'):
    prev = zlib.crc32(line, prev)
  return '{:08X}'.format(prev & 0xFFFFFFFF)


def report_not_a_dir(game_path, game_dir=None):
  _report_warning('could not find game directory: {}'.format(rel_dir(game_path, game_dir)))

def report_not_a_game(game_path, game_dir=None):
  _report_warning('not a game (no RPG_RT.ini found): {}'.format(rel_dir(game_path, game_dir)))

def report_no_assets(game_path, game_dir=None, audio=False, banner=False, icon=False, info=False):
  dir = rel_dir(game_path, game_dir)
  missing = [
    'audio.wav' if not audio else '',
    'banner.png' if not banner else '',
    'icon.png' if not icon else '',
    'info.cfg' if not info else ''
  ]
  missing = [a for a in missing if a]
  if len(missing) == 4:
    _report_warning('no 3DS assets found (see readme.md): {}'.format(path))
  _report_warning('3DS assets directory is missing files: {}: {}'.format(', '.join(missing), dir))

def report_no_info(game_path, game_dir=None, valid_id_length=None, valid_id=None, valid_title=None, valid_author=None):
  dir = rel_dir(game_path, game_dir)
  missing = [
    'invalid ID (must be hexadecimal)' if not valid_id else '',
    'invalid ID length (must be 6 characters)' if not valid_id_length else '',
    'invalid title' if not valid_title else '',
    'invalid author' if not valid_author else ''
  ]
  missing = [a for a in missing if a]
  _report_warning('info.cfg file is invalid or missing information: {}: {}'.format(', '.join(missing), dir))

def report_missing_prerequisites(has_bannertool, has_3dstool, has_sed, has_makerom):
  missing = [
    'bannertool' if not has_bannertool else '',
    '3dstool' if not has_3dstool else '',
    'makerom' if not has_makerom else '',
    'sed' if not has_sed else ''
  ]
  missing = [a for a in missing if a]
  _report_error('missing prerequisite{}: {}'.format('' if len(missing) == 1 else 's', ', '.join(missing)))

def report_default_assets(game_path, game_dir=None, items=[]):
  path = rel_dir(game_path, game_dir)
  _report_warning('game uses default assets{}: {}: {}'.format(' (a unique info.cfg file is required at minimum)' if 'info' in items else '', ', '.join(items), path))

def report_builds_done(count):
  _report('Built {} CIA file{} in total.'.format(count, '' if count == 1 else 's'))

def report_build_failed(game_path, game_dir=None):
  _report_warning('build failed for {}'.format(rel_dir(game_path, game_dir)))

def report_build_succeeded(result):
  date = result['game'].get('release_date')
  _report('Built {} as {}: #{} {} (by {}{})'.format(result['game']['name'], result['target'], result['game']['id'], result['game']['title'], result['game']['author'], ', {}'.format(date) if date else ''))

def _report_warning(str):
  print('build.py: Warning: {}'.format(str))

def _report_error(str):
  print('build.py: Error: {}'.format(str))
  sys.exit(1)

def _report(str):
  print(str)


if __name__ == "__main__":
  main()
