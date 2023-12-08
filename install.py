"""
Installation Helper

This script will create a virtual environment and install the dependencies
"""

import sys
import subprocess
import struct
import os

HERE = os.path.dirname(__file__)
REQUIREMENTS_TXT = os.path.join(HERE, 'requirements.txt')
ENVNAME = 'env'

# Check version of python
python_version = sys.version_info.major + 0.1 * sys.version_info.minor
env_32_or_64 = struct.calcsize("P") * 8

if (python_version < 3.10) or (env_32_or_64 != 32):
    version_string = str(python_version) + ' (' + str(env_32_or_64) + '-bit).'
    raise EnvironmentError('Must be run in Python 3.10 (32-bit). Current Version is ' + version_string)

print('Creating virtual environment...')
subprocess.check_call([sys.executable, '-m', 'venv', os.path.join(HERE, ENVNAME)])
env_executable = os.path.join(HERE, ENVNAME, 'Scripts', 'python.exe')
print('Installing dependencies vi PyPi...')
subprocess.check_call([env_executable, '-m', 'pip', 'install', '-r', REQUIREMENTS_TXT])