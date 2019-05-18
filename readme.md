## Easy3DS-build

A script for converting **RPG Maker 2000/2003 games** into **3DS games** using the [EasyRPG player](https://github.com/EasyRPG/Player). EasyRPG is an open source recreation of the RPG Maker engine, making it possible to play RPG Maker games on all modern operating systems and consoles—among them the 3DS.

The 3DS port of EasyRPG was made by Rinnegatamante in 2016 and has since become part of the EasyRPG main repository. The original announcements were made on [GBAtemp](https://gbatemp.net/threads/easyrpg-3ds-rpg-maker-2000-2003-player-for-3ds.419889/) and [the EasyRPG community forums](https://community.easyrpg.org/t/working-on-a-3ds-port/201/12).

The easiest way to play an RPG Maker game on the 3DS is to install a CIA file (which requires custom firmware; see the [3DS Hacks Guide](https://3ds.hacks.guide/) for setting it up). Converting an RPG Maker game into a CIA file requires a number of steps: **Easy3DS-build** does this work for you. All you need to do is provide the game, the required files, and a 3DS game icon and banner.

To run this script, the following dependencies are needed:

* [an EasyRPG build for 3DS (ELF file)](https://ci.easyrpg.org/job/player-3ds/)
* [`bannertool`](https://github.com/Steveice10/bannertool/releases)
* [`3dstool`](https://github.com/dnasdw/3dstool/releases)
* [`makerom`](https://github.com/profi200/Project_CTR/releases)
* the RPG Maker RTP files (2000 or 2003; unless your games don't need the RTP to run)

This script has no Python dependencies other than the standard library.

The EasyRPG ELF file can be found [on the EasyRPG CI server](https://ci.easyrpg.org/job/player-3ds/); or use [this direct link to the latest build](https://ci.easyrpg.org/job/player-3ds/lastSuccessfulBuild/artifact/builds/3ds/easyrpg-player.elf.zip).

Unfortunately I can't link to the RTP files directly as they can't be distributed legally. The EasyRPG project has been working on an [RTP replacement](https://github.com/EasyRPG/RTP) that is still in progress.

### Usage

This script can either build a single game, or build games in bulk. The easiest way to use this is to put all your games in the `games/` folder, add their 3DS assets (see "preparing assets") and then run the script:

```
./build.py games
```

This will run through every game folder and produce a CIA file for each one in the `out/` folder (by default).

### Default paths

To have the script find all dependencies automatically, without having to pass their locations, put them in the following locations:

* `assets/easyrpg-player.elf` - EasyRPG build
* `assets/RTP2000` - RPG Maker 2000 RTP
* `assets/RTP2003` - RPG Maker 2003 RTP

### Preparing assets

In order to build games for 3DS we'll need an **icon**, **banner** and **audio** file. These should be placed in a folder called `3DS` in the game's files. Additionally we need a **metadata** file named `info.cfg` which contains the title, author and a unique CIA ID.

You can copy over the default assets from `assets/defaults/` and edit them.

Your CIA ID will need to be unique or it will replace whatever other game uses it. Check the `titleid` column on [3DS DB](http://www.3dsdb.com/) to verify it.

#### RTP

For games that need the RTP to run, we'll copy over all RTP files that aren't already there before packaging. This way you don't need to worry about whether the RTP is installed on your 3DS. The CIA files are completely standalone.

If your game doesn't require the RTP to run, or you've already copied over all the files it needs, you need to make sure your `RPG_RT.ini` file has `FullPackageFlag=1` in it.

By default, the script will determine if your game has a 2000 or 2003 executable file, and then look for the appropriate RTP folder inside `assets` (named `RTP2000` and `RTP2003`).

### License

MIT
