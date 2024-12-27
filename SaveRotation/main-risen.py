import argparse
import shutil
import sys
import time
from glob import glob
from pathlib import Path
import zlib
import struct
import logging

from watchfiles import watch, Change

rotate_file_format = '{file_name}-{rotate}'

log = logging.getLogger("risen-rotater")
logging.basicConfig(stream=sys.stdout, level=logging.INFO)

def load_save(file_path: Path, rotation_number: int):
    """Loads a save file, decompresses, adjusts the save file name, compresses, and saves it as a new file."""
    log.debug(f"Loading file: {file_path}")

    file_name = file_path.stem

    with open(file_path, 'rb') as fh:
        contents = fh.read()

    signature, version, reserved, info_offset, layer_offset, object_offset = struct.unpack('8siiiii', contents[:28])
    decompressed = zlib.decompress(contents[info_offset:])
    version, name_size = struct.unpack('iH', decompressed[:6])

    # Fixed 2-byte width string
    new_save_name = b''
    for c in f'QuickSave - {rotation_number}':
        char = ord(c)
        # TODO: Test this with non-ascii characters
        if char < 255:
            to_add = c.encode('utf-8') + b'\x00'
        else:
            to_add = c.encode('utf-8')

        new_save_name += to_add

    # Make a backup just in case...
    shutil.copy(file_path, str(file_path) + '.bak')

    # Pack the new save header
    new_save_header = struct.pack(f'iH{len(new_save_name)}s', version, len(new_save_name), new_save_name)
    # Old save header size (1x 4-byte int, 1x 2-byte short)
    old_header_size = 6 + name_size
    # Diff between the two for the offsets
    header_size_diff = len(new_save_header) - old_header_size

    log.debug(f"Header size diff: {header_size_diff}")

    decompressed = new_save_header + decompressed[old_header_size:]
    #with open('out.txt', 'wb') as fh:
    #    fh.write(decompressed)

    compressed = zlib.compress(decompressed)

    new_file_name = str(file_path).replace(file_name, rotate_file_format.format(file_name=file_name, rotate=rotation_number))
    with open(new_file_name, 'wb') as fh:
        fh.write(struct.pack('8siiiii', signature, version, reserved, info_offset, layer_offset + header_size_diff, object_offset + header_size_diff))
        fh.write(compressed)

    log.info(f"New save file: {new_file_name}")


def main(file_path: Path):
    last_rotate = 0
    max_rotation = 100

    # Determine what our last_rotation should start as
    file_name = file_path.stem
    path = str(file_path).replace(file_path.name, '')
    glob_path = path + '*'
    files = glob(glob_path)

    for file in files:
        next_rotation_file = rotate_file_format.format(file_name=file_name, rotate=last_rotate + 1)
        if next_rotation_file in file:
            last_rotate += 1
            if last_rotate > max_rotation:
                last_rotate = 0
                break

    log.info(f"Last rotation set to {last_rotate}")

    while True:
        # Need to watch the directory, because risen deletes the file before creating a new one.
        log.info(f"Starting watch in {path} for {file_path.name}")
        watched_files = watch(path, step=250, rust_timeout=0)
        for changes in watched_files:
            for change_entry in changes:
                change = change_entry[0]
                file = change_entry[1]

                if file != str(file_path):
                    continue

                log.debug(f"Change: {change_entry}")

                # Some games delete their old file and make a new one
                if change == Change.deleted:
                    tries = 0
                    max_tries = 4

                    for i in range(max_tries):
                        if not file_path.exists():
                            time.sleep(0.5)
                            tries += 1

                    if tries >= max_tries:
                        exit_watch = True
                        break

                # new_file = file.replace(file_name, rotate_file_format.format(file_name=file_name, rotate=last_rotate+1))
                # shutil.copy(file, new_file)

                last_rotate += 1
                load_save(Path(file), last_rotate)

                if last_rotate > max_rotation:
                    log.info("Max rotation reached, resetting.")
                    last_rotate = 0

                # Need to re-watch the file
                if change == Change.deleted:
                    log.debug("Restarting watch")
                    time.sleep(1)
                    break



parser = argparse.ArgumentParser(
    prog='Save Rotation',
    description='Rotates files on modification. Intended to rotate quicksaves, so you don\'t lose progress.')
parser.add_argument('filename')

args = parser.parse_args()

file_path = Path(args.filename)

# load_save(file_path, 5)

main(file_path)
