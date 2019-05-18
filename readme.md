## Easy3DS-build

A simple script for building [EasyRPG games](https://github.com/EasyRPG/Player) for 3DS.

The 3DS port of EasyRPG was made by Rinnegatamante in 2016 and has since become part of the EasyRPG main code repository. The original announcements were made on [GBAtemp](https://gbatemp.net/threads/easyrpg-3ds-rpg-maker-2000-2003-player-for-3ds.419889/) and [the EasyRPG community forums](https://community.easyrpg.org/t/working-on-a-3ds-port/201/12). Easy3DS-build can run the build code for multiple games in bulk.

To run this script, the following dependencies are needed:

* [`bannertool`](https://github.com/Steveice10/bannertool/releases), [`3dstool`](https://github.com/dnasdw/3dstool/releases), [`makerom`](https://github.com/profi200/Project_CTR/releases)
* the EasyRPG repository (as submodule)

When cloning this repository, use `git clone --recurse-submodules -j8 URL` to get the EasyRPG submodule. If you already cloned this repository without submodules, run `git submodule update --init --recursive` to get it. This script has no Python dependencies other than the standard library.

### Usage

This script can either build a single game, or build games in bulk. The easiest way to use this is to put all your games in the `./games` folder, add their 3DS assets (see "preparing assets") and then run the script:

```
./build.py games
```

This will run through every game folder and produce a CIA file for each one in the `./out` directory (by default).

Note that it's assumed that you either have the RTP installed on your 3DS, or your game doesn't need the RTP to function. The easiest way to distribute games is to copy over all the RTP files that the game needs.

*TODO: describe how to do that.*

### Getting an EasyRPG ELF file

To build games, you'll need to put an EasyRPG build for 3DS in the assets folder. The latest nightly builds can be found [on the EasyRPG CI server](https://ci.easyrpg.org/job/player-3ds/); or use [this direct link to the latest build](https://ci.easyrpg.org/job/player-3ds/lastSuccessfulBuild/artifact/builds/3ds/easyrpg-player.elf.zip). Only the ELF file is needed.

### Preparing assets

In order to build games for 3DS we'll need an icon, banner and audio file. These should be placed in a folder called "3DS" in the game's files. Additionally we need an `info.cfg` file containing the game's title, author and a unique CIA ID.

You can copy over the default assets from `./assets/defaults` and edit them.

Your CIA ID will need to be unique or it will replace whatever other game uses it. Check the `titleid` column on [3DS DB](http://www.3dsdb.com/) to verify it.

### License

MIT
