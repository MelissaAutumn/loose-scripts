# Risen QuickSave Rotater

A hacky but functional QuickSave.save rotater! Turning 1 quick save into about 100 by default.

## But why?

I once quick saved during a battle, and it turns out the game doesn't pause the gameplay while the loading screen is up causing me to lose 3 minutes of progress. Annoyed, I spent the next several hours hacking this together. Time well spent if you ask me!

## Running

Install the requirements with pip:

```shell
pip install -r requirements.txt
```

And then run the script with a filename like:

```shell
python main-risen.py /home/melissaa/steam/steam/steamapps/compatdata/40300/pfx/drive_c/users/steamuser/AppData/Local/Risen/SaveGames/QuickSave.save
```

As you quick save (or over-write an existing save if you have it set to a different save file) this script should load that new quick save, adjust the save file name, and save it as a new file like `QuickSave-1.save`. If you need to access it, just restart the game and it should show up in your save game list.


## Quirks

Risen doesn't reload the save game list on external file changes. In order to see your quick save you'll need to restart. Think of them as backups.

I also adjust the save name in the savefile itself (before I realized Risen needs to be restarted...) and haven't tested actual 2-byte utf-8 characters..so ymmv.

## Special Thanks

- https://github.com/wiktorek140/RisenSaveEditor/tree/master for documenting the save format.