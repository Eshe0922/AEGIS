import subprocess
import os
import re
import enum
import difflib
import os
import json
import requests
import time
from pathlib import Path
import tempfile

TIME_OUT_LABEL= ' seconds. Partial output:'
DIFF_FENCE = ["```diff", "```"]
BASH_FENCE = ["```bash", "```"]
HEAD = "<<<<<<< SEARCH"
DIVIDER = "======="
UPDATED = ">>>>>>> REPLACE"

class RESULT(enum.Enum):
    SUCCEED=1
    FAILED=2

def remove_patches_to_tests(model_patch):
    lines = model_patch.splitlines(keepends=True)
    filtered_lines = []
    is_tests = False

    for line in lines:
        if line.startswith("diff --git a/"):
            pieces = line.split()
            to = pieces[-1]
            if to.startswith("b/") and (
                "/test/" in to
                or "/tests/" in to
                or "/testing/" in to
                or "/test_" in to
                or "/tox.ini" in to
            ):
                is_tests = True
            else:
                is_tests = False

        if not is_tests:
            filtered_lines.append(line)

    return "".join(filtered_lines)

def extract_diffs(text):
    pattern = rf'{DIFF_FENCE[0]}([\s\S]*?){DIFF_FENCE[1]}'
    matches = re.findall(pattern, text)
    diffs = ''
    if len(matches) > 0:
        diffs = matches[0]
    return diffs

def extract_states(text):
    if '### State:' in text: 
        state = text.split('### State:')[-1].split('\n')[0].strip()
        return state
    return ''

def extract_commands(text):
    pattern = rf'{BASH_FENCE[0]}([\s\S]*?){BASH_FENCE[1]}'
    matches = re.findall(pattern, text)
    command_text = ''
    if len(matches) > 0:
        command_text = matches[0]

    commands = []
    if command_text:
        commands = list(filter(None, command_text.split('\n')))
    return commands


def extract_explain(text):
    if "Explanation:" in text:
        return text.split('Explanation:')[-1]
    else:
        return None
    
def extract_thought_codes(text):
    if len(text) > 1:
        code_snippet_pattern = re.compile(r'(\S+)\s+(\d+)~(\d+)')
        matched_snippets = code_snippet_pattern.findall(text)
        if matched_snippets:
            code_snippets = []
            for match in matched_snippets:
                file_path, start_line, end_line = match
                snippet_info = {
                    "file_path": file_path,
                    "start_line": int(start_line),
                    "end_line": int(end_line),
                }
                code_snippets.append(snippet_info)
            print("Thought code snippet:\n")
            for snippet in code_snippets:
                print(snippet)
            return code_snippets
        else:
            return None
    else:
        print("*******************")
        print(text)
        return None

def extract_thought(text):
    if "Thought:" in text:
        return text.split("Thought:")[-1].split("Action:")[0]
    else:
        return None
    
def extract_codes(text):
    if re.search(r'#{1,3}\s*Result:', text, re.IGNORECASE):
        if "Explanation:" in text:
            text = text.split("Explanation:")[0]
            pattern = re.compile(r'(\S+)\s+(\d+)[~-—](\d+)')
            matches = pattern.findall(text)
            if matches:
                code_snippets = []
                for match in matches:
                    file_path, start_line, end_line = match
                    snippet_info = {
                        "file_path": file_path,
                        "start_line": int(start_line),
                        "end_line": int(end_line),
                    }
                    code_snippets.append(snippet_info)
                print("Result code snippet:\n")
                for snippet in code_snippets:
                    print(snippet)
                return code_snippets
            else:
                return None
        else:
            return None
    else:
        return None

def extract_result(text):
    match = re.search(r"###\s*result:\s*(success|succeed|successfully|successful|failed|fail|failure)", text, re.IGNORECASE)

    if match:
        result = match.group(1)
        if result.lower() in {'succeed', 'successful', 'success', 'successfully'}:
            return RESULT.SUCCEED
        elif result.lower()in {'failed', 'fail', 'failure'}:
            return RESULT.FAILED
        else:
            return None
    else:
        return None

def extract_reproduce_judger_result(text):
    match = re.search(r"###\s*result:\s*(True|False)", text, re.IGNORECASE)

    if match:
        result = match.group(1)
        if result.lower() == 'true':
            return True
        elif result.lower() == 'false':
            return False
        else:
            return None
    else:
        return None

def append_trajectory(trajectory, messages, agent: str):
    for message in messages:
        message['agent'] = agent.lower()
        trajectory.append(message)

def save_trajectory(instance_id, traj_dir, trajectory):
    trial_index = 1
    def get_unique_filename(traj_dir, trial_index):
        filename = f"{instance_id}_{trial_index}.txt"
        while os.path.exists(os.path.join(traj_dir, filename)):
            trial_index += 1
            filename = f"{instance_id}_{trial_index}.txt"
        return filename
    
    traj_file = get_unique_filename(traj_dir, trial_index)
    trajectory_json = json.dumps(trajectory, indent=4, sort_keys=True, ensure_ascii=False)
    with open(os.path.join(traj_dir, traj_file), 'a', encoding='utf-8') as file:
        file.write(f"{trajectory_json}\n")

def save_reproduce(instance_id, reproduce_dir, reproduce):
    trial_index = 1
    def get_unique_filename(traj_dir, trial_index):
        filename = f"{instance_id}_{trial_index}.py"
        while os.path.exists(os.path.join(traj_dir, filename)):
            trial_index += 1
            filename = f"{instance_id}_{trial_index}.py"
        return filename
    
    reproduce_file = get_unique_filename(reproduce_dir, trial_index)
    with open(os.path.join(reproduce_dir, reproduce_file), 'w', encoding='utf-8') as file:
        file.write(reproduce)
        
def save_diff_description(text):
    temp_dir = "/tmp/patch"
    os.makedirs(temp_dir, exist_ok=True)
    cmd = f"sudo chmod -R 777 {temp_dir}"
    subprocess.run(cmd, check=True, shell=True)
    with tempfile.NamedTemporaryFile(mode='w+', dir=temp_dir, delete=False) as temp_file:
        temp_file_path = temp_file.name
        os.chmod(temp_file_path, 0o777)
        temp_file.write(text)
    return temp_file_path


