#!/usr/bin/env python3.8
"""
main module of the reworked evaluation script
"""
import os

import check

if __name__ == "__main__":
    with check.LockFile(check.LOCK_FILE_PATH):
        check.run()
