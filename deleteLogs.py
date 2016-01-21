import os
import glob
import time

now = time.time()

files = glob.glob('C:\Users\Administrator\Desktop\logsXtento\*')

for f in files:
  if os.stat(f).st_mtime < now - 60 * 86400:
    os.remove(f)
