import shutil
root = r"/mnt/data/release-notes-generator"
shutil.make_archive(root, 'zip', root)
print('Created', root + '.zip')
