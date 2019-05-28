# #!/usr/bin/env python
# # coding=utf-8
from store_and_convert import mymain,allowed_file_conversion
from supplement import *
from stat import S_ISREG, ST_CTIME, ST_MODE ,ST_MTIME
import os, sys, time , shutil

allowed_file_types = allowed_file_conversion()
# path to the directory (relative or absolute)
dirpath = path_to_outputs
# path to destination folder
destination = path_to_project

# get all entries in the directory w/ stats
entries = (os.path.join(dirpath, fn) for fn in os.listdir(dirpath))
entries = ((os.stat(path), path) for path in entries)

# leave only regular files, insert creation date
entries = ((stat[ST_MTIME], path)
	for stat, path in entries if S_ISREG(stat[ST_MODE]))
#ST_MTIME sort by modification date
#ST_CTIME sort by a creation date

for cdate, path in sorted(entries):
	file = os.path.join(path_to_outputs,os.path.basename(path))
	#check if file is in allowed file types and if it is send it to destination to run store_and_convert.py
	for allowed_file_type in allowed_file_types:
		if file.endswith(allowed_file_type):
			print(os.path.basename(path))
			shutil.move(file,destination)
			print('Transfer to project')
			mymain()


