#!/usr/bin/env python3

import argparse
import configparser
import os
import re
import shutil
import subprocess
import sys
import unicodedata
import zlib
from distutils.dir_util import copy_tree
from distutils.spawn import find_executable
from glob import glob

# List of all known RTP versions. See readme.md for downloads.
RTP_VERSIONS = {
  '2000-jp': 'RPG Maker 2000 - Japanese (original)',
  '2000-en-don-miguel': 'RPG Maker 2000 - English (Don Miguel)',
  '2000-en-official': 'RPG Maker 2000 - English (official)',
  '2003-jp': 'RPG Maker 2003 - Japanese (original)',
  '2003-en-rpg-advocate': 'RPG Maker 2003 - English (RPG Advocate)',
  '2003-ru-kovnerov': 'RPG Maker 2003 - Russian (Vlad Kovnerov)',
  '2003-en-official': 'RPG Maker 2003 - English (official)',
  '2003-en-maker-universe': 'RPG Maker 2003 - English (Maker Universe)',
  '2003-ko-nioting': 'RPG Maker 2003 - Korean (니오팅)',
  'easyrpg': 'EasyRPG RTP replacement project'
}


def make_cia_file(id, title, author, release_date, game_path, name, safe_name, banner, audio, icon, elf, spec, tmp, out, rel_dir):
  '''
  Actually builds the CIA file. This procedure creates temporary files that aren't cleaned up here.
  '''
  success = True
  
  result = subprocess.run(['bannertool', 'makebanner', '-i', banner, '-a', audio, '-o', tmp + '/banner.bin'], capture_output=True)
  if result.returncode != 0: return report_cia_error(1, 'makebanner', rel_dir)
  result = subprocess.run(['bannertool', 'makesmdh', '-s', title, '-l', title, '-p', author, '-i', icon, '-o', tmp + '/icon.bin'], capture_output=True)
  if result.returncode != 0: return report_cia_error(2, 'makesmdh', rel_dir)
  result = subprocess.run(['3dstool', '-cvtf', 'romfs', tmp + '/romfs.bin', '--romfs-dir', game_path], capture_output=True)
  if result.returncode != 0: return report_cia_error(3, '3dstool', rel_dir)

  try:
    with open(spec, 'r') as fp:
      spec_txt = fp.read()
    with open(tmp + '/spec.rsf', 'w') as fp:
      fp.write(spec_txt.replace('{{UNIQUE_ID}}', id))
  except:
    return report_cia_error(4, 'rsf', rel_dir)
  
  result = subprocess.run(['makerom', '-f', 'cia', '-o', out + '/' + safe_name + '.cia', '-elf', elf, '-rsf', tmp + '/spec.rsf', '-icon', tmp + '/icon.bin', '-banner', tmp + '/banner.bin', '-exefslogo', '-target', 't', '-romfs', tmp + '/romfs.bin'], capture_output=True)
  if result.returncode != 0: return report_cia_error(5, 'makerom', rel_dir)

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
    if os.path.isdir(file):
      shutil.rmtree(file)
    else:
      os.remove(file)


def build_cia(base, game_path, game_name, elf_path, rtp_dirs, no_rtp, spec_path, out_dir, tmp_dir, default_crcs, game_dir=None):
  '''
  Prepares to build a CIA file by assembling all the information needed.
  '''
  assets_path = '{}/3DS/'.format(game_path)
  safe_name = slugify(game_name)
  target = '{}/{}.cia'.format(out_dir, safe_name)
  rel_path = rel_dir(game_path, game_dir)
  rel_target = rel_dir(target, out_dir)

  rpg_rt = get_config(game_path + '/RPG_RT.ini')['RPG_RT']
  full_package_flag = rpg_rt.get('FullPackageFlag', '').strip() == '1'
  info = get_config(assets_path + 'gameinfo.cfg')['metadata']
  wanted_rtp = info.get('rtp', '').strip()

  # Warn if the game doesn't have a FullPackageFlag but the user passed --no-rtp.
  if not full_package_flag and no_rtp:
    report_rtp_needed(wanted_rtp, game_path, game_dir)

  # Check if we have the necessary RTP version.
  if not rtp_dirs.get(wanted_rtp) and not no_rtp and not full_package_flag:
    fallback = get_rtp_fallback(rtp_dirs, wanted_rtp, game_path)
    if fallback:
      report_rtp_fallback(wanted_rtp, fallback, game_path, game_dir)
      wanted_rtp = fallback
    else:
      report_no_rtp_for_game(wanted_rtp, game_path, game_dir)
      return {
        'success': False,
        'skip': True,
        'dir': rel_path,
        'target': rel_target
      }

  # Check whether this game is using any of the default assets.
  # This raises a warning; if a default gameinfo.cfg is found, we fail the build.
  crcs = {
    'audio': crc(assets_path + 'audio.wav'),
    'banner': crc(assets_path + 'banner.png'),
    'icon': crc(assets_path + 'icon.png'),
    'info': crc(assets_path + 'gameinfo.cfg')
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
      # Make a temp dir, then copy over the RTP and finally the game.
      game_tmp_dir = make_game_tmp(safe_name, tmp_dir)
      copy_rtp_to_tmp(game_tmp_dir, wanted_rtp, rtp_dirs)
      copy_game_to_tmp(game_tmp_dir, game_path)

      # Author is optional.
      author = info.get('author').strip()
      
      # Use this to make the CIA file.
      game = make_cia_file(
        info.get('cia_id').strip(),
        info.get('title').strip(),
        author if author else 'Unknown author',
        info.get('release', '').strip(),
        game_tmp_dir,
        game_name,
        safe_name,
        assets_path + 'banner.png',
        assets_path + 'audio.wav',
        assets_path + 'icon.png',
        elf_path,
        spec_path,
        tmp_dir,
        out_dir,
        rel_dir(game_path, game_dir)
      )
      success = game['success']
    except:
      success = False
    finally:
      clean_up_tmp_files(tmp_dir)

  return {
    'success': success,
    'full_package_flag': full_package_flag,
    'no_rtp': no_rtp,
    ''
    'dir': rel_path,
    'target': rel_target,
    'game': game
  }


def main():
  '''
  Script main entry point. Parses command-line arguments.
  '''
  parser = argparse.ArgumentParser(description='Script for generating 3DS CIA files from RPG Maker 2000 games using EasyRPG. See readme.md for setting up the build requirements. Only the source directory needs to be specified; defaults will be used for everything else.')

  parser.add_argument('dir', type=str, help='source dir containing an RM2K(3) game, or multiple games')
  parser.add_argument('--elf', type=str, help='path to an EasyRPG ELF file', default='./assets/easyrpg-player.elf')
  parser.add_argument('--spec', type=str, help='path to a ROM spec file (will get a new unique ID)', default='./assets/spec.rsf')
  parser.add_argument('--rtp', type=str, help='path to the directory containing RTPs', default='./assets/rtp')
  parser.add_argument('--no-rtp', action='store_true', help='don\'t copy RTP files when packaging', default=False)
  parser.add_argument('--out', type=str, help='CIA file output dir', default='./out')
  args = parser.parse_args()
  base = os.path.abspath(os.path.dirname(sys.argv[0]))
  tmp_dir = base + '/tmp'

  rtp = check_rtp(args.rtp)
  check_rsf_template(args.spec)
  check_prerequisites()
  check_easyrpg_elf(args.elf)
  clean_up_tmp_files(tmp_dir)

  build_dir(base, args.dir, args.elf, rtp, args.no_rtp, args.spec, args.out, tmp_dir)
  sys.exit(0)


def build(base, item, game_dir, elf_path, rtp_dirs, no_rtp, spec_path, out_dir, tmp_dir, report_dir=False):
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
    'info': crc(default_base + 'gameinfo.cfg')
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
  result = build_cia(base, game_path, item, elf_path, rtp_dirs, no_rtp, spec_path, out_dir, tmp_dir, defaults, game_dir)
  if not result['success']:
    if result.get('skip'):
      return result
    report_build_failed(game_path, game_dir)
  else:
    report_build_succeeded(result)
  return result

def build_dir(base, game_dir, elf_path, rtp_dirs, no_rtp, spec_path, out_dir, tmp_dir):
  '''
  Builds either a single game or multiple games.
  '''
  # Check if we're building one game or multiple games.
  if is_game(game_dir):
    bits = os.path.split(game_dir)
    item = bits[1]
    result = build(base, item, game_dir, elf_path, rtp_dirs, no_rtp, spec_path, out_dir, tmp_dir, True)
    if result and result['success']:
      return
    else:
      sys.exit(1)

  count = 0
  for item in os.listdir(game_dir):
    result = build(base, item, game_dir, elf_path, rtp_dirs, no_rtp, spec_path, out_dir, tmp_dir, False)
    if result and result['success']:
      count += 1

  report_builds_done(count)


def make_game_tmp(name, tmp_dir):
  tmp = '{}/{}'.format(tmp_dir, name)
  return tmp


def copy_rtp_to_tmp(tmp_path, wanted_rtp, rtp_dirs):
  '''Copies an RTP to the temp directory.'''
  rtp_path = rtp_dirs.get(wanted_rtp)
  if rtp_path:
    copy_tree(rtp_path, tmp_path)


def copy_game_to_tmp(tmp_path, game_path):
  '''Copies a game to the temp directory.'''
  copy_tree(game_path, tmp_path)


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
  info = os.path.isfile(base + 'gameinfo.cfg')
  if not (audio and banner and icon and info):
    report_no_assets(dir, game_dir, audio, banner, icon, info)
    return False
  return True


def check_3ds_info(dir, game_dir):
  '''Checks if a game's gameinfo.cfg file contains all required information. Warns otherwise.'''
  c = get_config('{}/3DS/gameinfo.cfg'.format(dir))['metadata']
  id = c['cia_id']
  title = c['title']
  author = c.get('author')
  if not author:
    author = 'Unknown author'

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


def check_rtp(rtp):
  has_rtp_dir = os.path.isdir(rtp)
  if not has_rtp_dir:
    _report_warning('could not find RTP directory: {}'.format(rtp))
    return
  
  rtps = {}
  for item in os.listdir(rtp):
    path = rtp + '/' + item
    if os.path.isdir(path):
      rtps[item] = path
  
  if len(rtps.keys()) == 0:
    _report_warning('could not find any RTPs: {}'.format(rtp))
  
  return rtps


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
  has_makerom = bin_is_available('makerom')

  if not (has_bannertool and has_3dstool and has_makerom):
    report_missing_prerequisites(has_bannertool, has_3dstool, has_makerom)
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


def get_rm_version(game_path):
  '''Checks what version of the RPG Maker RTP this game needs.'''
  exe = game_path + '/RPG_RT.exe'
  if not os.path.isfile(exe):
    # If we don't have an executable file at all, just pretend it's 2003.
    # 2003 is the more compatible RTP since it works for both 2000 and 2003 games.
    return 2003
  
  # Note: this is not very accurate.
  # 2000 executables tend to be around 730 KB, and 2003 executables around 950 KB.
  size = os.path.getsize(exe)
  if size > 800000:
    return 2003
  else:
    return 2000


def get_rtp_fallback(rtps, wanted_rtp, game_path):
  '''
  Returns an alternative RTP if we can't find the exact one.
  '''
  wanted = ''
  if wanted_rtp.startswith('2000-en'):
    wanted = '2000-en'
  if wanted_rtp.startswith('2003-en'):
    wanted = '2003-en'
  
  if not wanted:
    rm = get_rm_version(game_path)
    if rm == 2000:
      wanted = '2000-en'
    else:
      wanted = '2003-en'
  
  if wanted == '2000-en':
    if rtps.get('2000-en-don-miguel'): return '2000-en-don-miguel'
    if rtps.get('2000-en-official'): return '2000-en-official'
  if wanted == '2003-en':
    if rtps.get('2003-en-rpg-advocate'): return '2003-en-rpg-advocate'
    if rtps.get('2003-en-maker-universe'): return '2003-en-maker-universe'
    if rtps.get('2003-en-official'): return '2003-en-official'
  
  return False


def report_rtp_needed(wanted_rtp, game_path, game_dir=None):
  _report_warning('game needs RTP but --no-rtp was passed: {}{}'.format(rel_dir(game_path, game_dir), ' (needed: {})'.format(wanted_rtp) if wanted_rtp else ''))

def report_not_a_dir(game_path, game_dir=None):
  _report_warning('could not find game directory: {}'.format(rel_dir(game_path, game_dir)))

def report_not_a_game(game_path, game_dir=None):
  _report_warning('not a game (no RPG_RT.ini found): {}'.format(rel_dir(game_path, game_dir)))

def report_no_rtp_for_game(rtp, game_path, game_dir=None):
  _report_warning('game needs {} (skipping): {}'.format('an RTP, but none were found' if not rtp else 'the {} RTP which we don\'t have, and no fallback was found'.format(rtp), rel_dir(game_path, game_dir)))

def report_rtp_fallback(rtp, fallback, game_path, game_dir=None):
  if rtp:
    _report_warning('game needs the {} RTP which we don\'t have; fallback {} RTP will be used: {}'.format(rtp, fallback, rel_dir(game_path, game_dir)))
  else:
    _report_warning('game needs an RTP but doesn\'t indicate which one; {} RTP will be used: {}'.format(fallback, rel_dir(game_path, game_dir)))

def report_no_assets(game_path, game_dir=None, audio=False, banner=False, icon=False, info=False):
  dir = rel_dir(game_path, game_dir)
  missing = [
    'audio.wav' if not audio else '',
    'banner.png' if not banner else '',
    'icon.png' if not icon else '',
    'gameinfo.cfg' if not info else ''
  ]
  missing = [a for a in missing if a]
  if len(missing) == 4:
    _report_warning('no 3DS assets found (skipping): {}'.format(dir))
    return
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
  _report_warning('gameinfo.cfg file is invalid or missing information: {}: {}'.format(', '.join(missing), dir))

def report_missing_prerequisites(has_bannertool, has_3dstool, has_makerom):
  missing = [
    'bannertool' if not has_bannertool else '',
    '3dstool' if not has_3dstool else '',
    'makerom' if not has_makerom else ''
  ]
  missing = [a for a in missing if a]
  _report_error('missing prerequisite{}: {}'.format('' if len(missing) == 1 else 's', ', '.join(missing)))

def report_default_assets(game_path, game_dir=None, items=[]):
  path = rel_dir(game_path, game_dir)
  _report_warning('game uses default assets{}: {}: {}'.format(' (a unique gameinfo.cfg file is required at minimum)' if 'info' in items else '', ', '.join(items), path))

def report_cia_error(step, type, rel_path):
  _report_warning('build failed at step {} ({}) for {}'.format(step, type, rel_path))

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
