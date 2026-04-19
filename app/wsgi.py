import sys
path = '/home/USERNAME/.local/lib/python3.9/site-packages'
sys.path.insert(0, path)

from app import app as application
