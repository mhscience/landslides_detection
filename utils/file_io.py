import os


def remove_files(files):
    for f in files:
        os.remove(f)