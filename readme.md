## Easy3DS-build

A script for converting **RPG Maker 2000/2003 games** into **3DS games** using the [EasyRPG player](https://github.com/EasyRPG/Player). EasyRPG is an open source recreation of the RPG Maker engine, making it possible to play RPG Maker games on all modern operating systems and consoles—among them the 3DS.

The 3DS port of EasyRPG was made by Rinnegatamante in 2016 and has since become part of the EasyRPG main repository. The original announcements were made on [GBAtemp](https://gbatemp.net/threads/easyrpg-3ds-rpg-maker-2000-2003-player-for-3ds.419889/) and [the EasyRPG community forums](https://community.easyrpg.org/t/working-on-a-3ds-port/201/12).

The easiest way to play an RPG Maker game on the 3DS is to install a CIA file (which requires custom firmware; see the [3DS Hacks Guide](https://3ds.hacks.guide/) for setting it up). Converting an RPG Maker game into a CIA file requires a number of steps: **Easy3DS-build** does this work for you. All you need to do is provide the game, the required files, and a 3DS game icon and banner.

To run this script, the following dependencies are needed:

* [an EasyRPG build for 3DS (ELF file)](https://ci.easyrpg.org/job/player-3ds/)
* [`bannertool`](https://github.com/Steveice10/bannertool/releases)
* [`3dstool`](https://github.com/dnasdw/3dstool/releases)
* [`makerom`](https://github.com/profi200/Project_CTR/releases)
* the appropriate RPG Maker RTP files (unless your games don't need the RTP to run)

This script has no Python dependencies other than the standard library.

The EasyRPG ELF file can be found [on the EasyRPG CI server](https://ci.easyrpg.org/job/player-3ds/); or use [this direct link to the latest build](https://ci.easyrpg.org/job/player-3ds/lastSuccessfulBuild/artifact/builds/3ds/easyrpg-player.elf.zip).

### Usage

This script can either build a single game, or build games in bulk. The easiest way to use this is to put all your games in the `games/` folder, add their 3DS assets (see "preparing assets") and then run the script:

```
./build.py games
```

This will run through every game folder and produce a CIA file for each one in the `out/` folder. Temp files will be written to `tmp/` and removed after the build finishes.

To have the script find all dependencies automatically, without having to pass them as arguments, put them in the following locations:

* `assets/easyrpg-player.elf` - EasyRPG build
* `assets/RTP` - RPG Maker RTP packages

### RTP

For games that need the RTP to run, we'll copy over all RTP files that aren't already there before packaging. This way you don't need to worry about whether the RTP is installed on your 3DS. The CIA files are completely standalone.

If your game doesn't require the RTP to run, or you've already copied over all the files it needs, you need to make sure your `RPG_RT.ini` file has `FullPackageFlag=1` in it.

Traditionally, the RTP poses one unfortunate problem: there are multiple different versions of the RTP that are not compatible with each other. Each game you want to build might need a different version. Fortunately, EasyRPG has solved this problem, as long as you have the official (and freely available) RTP and a recent build. Even if a game requires e.g. Don Miguel's RTP, and you have the official RTP installed, the engine will rename all its file requests to match the installed RTP.

**In short: just get the English RTPs listed as "official" and it should work**—unless the game uses non-standard additions such as Don Miguel's RTP extras (RTP 1.32).

These are all the known RTPs:

| Code | Version | Download |
|:-----|:-----|:---------|
| 2000-jp | RPG Maker 2000 - Japanese (original) | [tkool.jp](http://tkool.jp/support/download/rpg2000/rtp) |
| 2000-en-don-miguel | RPG Maker 2000 - English (Don Miguel)<br>*Most common variant for non-Japanese 2000 games* | - |
| **2000-en-official** | **RPG Maker 2000 - English (official)**<br>*Download this for non-Japanese games* | **[rpgmakerweb.com](http://www.rpgmakerweb.com/download/additional/run-time-packages)** |
| 2003-jp | RPG Maker 2003 - Japanese (original) | [tkool.jp](http://tkool.jp/support/download/rpg2003/rtp) |
| 2003-en-rpg-advocate | RPG Maker 2003 - English (RPG Advocate)<br>*Most common variant for non-Japanese 2003 games* | - |
| 2003-ru-kovnerov | RPG Maker 2003 - Russian (Vlad Kovnerov) | [rpgmaker.su](http://rpgmaker.su/vbdownloads.php?do=download&downloadid=22) |
| **2003-en-official** | **RPG Maker 2003 - English (official)**<br>*Download this for non-Japanese games* | **[rpgmakerweb.com](http://www.rpgmakerweb.com/download/additional/run-time-packages)** |
| 2003-en-maker-universe | RPG Maker 2003 - English (Maker Universe) | - |
| 2003-ko-nioting | RPG Maker 2003 - Korean (니오팅) | [etude87.tistory.com](http://etude87.tistory.com/161) |
| easyrpg | EasyRPG RTP replacement project | [github.com](https://github.com/EasyRPG/RTP) |

Put your RTP in the `assets/rtp/` folder, and name the folder after the "code" listed in the table above. The RTP must be unzipped - an installer EXE file won't work. The official RTP files hosted on rpgmakerweb.com can be extracted as though they are 7z files. On Mac OS X, [The Unarchiver](https://theunarchiver.com/) can extract them as well.

For games that don't indicate what RTP they need (and don't have the `FullPackageFlag=1` set), this script will check for a 2000 or 2003 executable file and then load any English RTP that is available for that version.

### Preparing assets and `gameinfo.cfg`

In order to build games for 3DS we'll need an **icon**, **banner** and **audio** file. These should be placed in a folder called `3DS` in the game's files. Additionally we need a **metadata** file named `gameinfo.cfg` which contains the title, author and a unique CIA ID.

You can copy over the default assets from `assets/defaults/` and edit them. Here's an example `gameinfo.cfg` file:

```ini
[metadata]
cia_id = 8D29C9
title = Don's Adventures
author = Don Miguel
release = 2000
rtp = 2000-en-don-miguel
```

Your CIA ID can be any random hexadecimal number, but it will need to be unique or installing it might replace another game or application. Check the `titleid` column on [3DS DB](http://www.3dsdb.com/) to verify it.

### License

MIT
