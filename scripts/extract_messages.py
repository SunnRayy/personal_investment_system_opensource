#!/usr/bin/env python3
"""Extract translatable strings from the codebase."""

import os
import re
import subprocess
import sys

def extract_messages():
    """Run pybabel extract to find all translatable strings."""
    cmd = [
        'pybabel', 'extract',
        '-F', 'babel.cfg',
        '-o', 'translations/messages.pot',
        '--add-comments=NOTE',
        '--sort-output',
        '.'
    ]
    subprocess.run(cmd, check=True)
    print("Extracted messages to translations/messages.pot")

def init_locale(locale: str):
    """Initialize a new locale."""
    cmd = [
        'pybabel', 'init',
        '-i', 'translations/messages.pot',
        '-d', 'translations',
        '-l', locale
    ]
    subprocess.run(cmd, check=True)
    print(f"Initialized locale: {locale}")

def compile_messages():
    """Compile all message catalogs."""
    cmd = ['pybabel', 'compile', '-d', 'translations']
    subprocess.run(cmd, check=True)
    print("Compiled all translations")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == 'extract':
            extract_messages()
        elif sys.argv[1] == 'init' and len(sys.argv) > 2:
            init_locale(sys.argv[2])
        elif sys.argv[1] == 'compile':
            compile_messages()
    else:
        print("Usage: python scripts/extract_messages.py [extract|init <locale>|compile]")
