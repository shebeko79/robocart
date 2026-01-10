import os
import sys

if len(sys.argv) < 2:
    print(f"Use: {sys.argv[0]} <file_name.key>")
    exit(1)

bts = os.urandom(16)
with open(sys.argv[1], 'wb') as file:
    file.write(bts)
