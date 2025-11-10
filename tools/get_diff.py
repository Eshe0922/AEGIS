# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Xinchen Wang 王欣辰

import argparse
import subprocess
import os
def git_diff_to_patch(project_path):
    try:
        os.chdir(project_path)
        stdout = subprocess.check_output(['git', '--no-pager', 'diff']).decode()
        print(stdout)
        
    except Exception as error:
        print("git diff error: ", error)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='get diff in repo.')
    parser.add_argument('-p', '--project_path', help='Name of the class', required=True)
    args = parser.parse_args()
    git_diff_to_patch(args.project_path)