#!/usr/bin/env python3
"""
run all tests for memory scramble game.
just run this script to run the whole test suite.
"""

import subprocess
import sys
import os

def main():
    # find the project root (where test/ is)
    os.chdir(os.path.dirname(os.path.dirname(__file__)))

    # run pytest on test directory
    result = subprocess.run([
        sys.executable, '-m', 'pytest', 'test/', '-v', '--tb=short'
    ], capture_output=True, text=True)

    print(result.stdout)
    if result.stderr:
        print("errors:", result.stderr)

    return result.returncode

if __name__ == '__main__':
    sys.exit(main())
