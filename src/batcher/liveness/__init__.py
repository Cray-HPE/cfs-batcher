import os

WORKING_DIRECTORY = '/var/'
TIMESTAMP_PATH = os.path.join(WORKING_DIRECTORY, 'timestamp')

try:
    os.makedirs(WORKING_DIRECTORY)
except FileExistsError:
    pass

