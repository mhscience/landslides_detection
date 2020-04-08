import os

def remove_files(files):
    for f in files:
        os.remove(f)

def recreate_folder(folder):
    if not os.path.exists(folder):
        os.makedirs(folder)
