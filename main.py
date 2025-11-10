# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Xinchen Wang 王欣辰

import os, sys
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from agents.reproducer_refine import Reproducer
from utils.sandbox import Sandbox
from utils.agent_util import save_trajectory, save_reproduce
import argparse
import json
import multiprocessing
import os
import sys
from datetime import datetime
import time

def run_reproduce_task_multi(args, item, index):
    output_path = args.output_path

    item = item[0]
    namespace = item[1]
    output_file_path = os.path.join(output_path, f'task_{item["instance_id"]}.log')

    with open(output_file_path, 'w') as log_file:
        sys.stdout = log_file
        try:
            begin = datetime.now()
            datetime_str_begin = begin.strftime('%Y %m %d %H %M %S')
            print(f"#### start time: {datetime_str_begin}")
            retry = 3
            current_try = 0
            while(current_try < retry):
                current_try += 1
                try:
                    trajectory = []
                    sandbox = Sandbox(namespace, item)
                    sandbox.start_container()
                    project_path = sandbox.get_project_path()
                    reproducer = Reproducer(sandbox)
                    problem_statement = item["title"] + '\n' +  item["body"]
                    reproduce_command, reproduce_message, reproduce_content, reproduce_path, trajectory, reproduce_contents = reproducer.run(project_path,problem_statement, trajectory)
                    save_reproduce(instance_id = item["instance_id"], reproduce_dir = args.patches_path, reproduce = reproduce_content)
                    save_trajectory(instance_id = item["instance_id"], traj_dir = args.log_path, trajectory=trajectory)
                    sandbox.stop_container()

                except Exception as e:
                    print(f"Error occurred: {e}")
                    if "Failed to get response from LLM" in str(e) or "Token limit protect!" in str(e):
                        time.sleep(60)
                        sandbox.stop_container()
                        continue
                    else:
                        sandbox.stop_container()
                        break

            end = datetime.now()
            datetime_str_end = end.strftime('%Y %m %d %H %M %S')
            print(f"#### end time: {datetime_str_end}")
            print(f"This instance has been successfully resolved!!")
        finally:
            sys.stdout = sys.__stdout__

def worker(task_queue):
    while True:
        task = task_queue.get()
        if task is None:
            break
        args, item, index = task
        run_reproduce_task_multi(args, item, index)

def main(args):
    num_processes = 6 
    num_tasks = 300
    task_queue = multiprocessing.Queue()
    
    pool = []
    for _ in range(num_processes):
        p = multiprocessing.Process(target=worker, args=(task_queue,))
        p.start()
        pool.append(p)

    jsonList = []

    with open(args.instances_path, 'r') as file:
        rawdata = file.readlines()
        for line in rawdata:
            data = json.loads(line)
            data['instance_id'] = data['id'].replace('/','_')
            
            # 预先构建好项目仓库的Docker镜像 !!!
            image = "TODO"
            jsonList.append((data, image))

    tasks = [(args, jsonList[i], i+1) for i in range(len(jsonList))]
    print(len(tasks))

    for task in tasks:
        task_queue.put(task)
    
    for _ in range(num_processes):
        task_queue.put(None)

    for p in pool:
        p.join()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Script to handle paths.")
    parser.add_argument("--instances_path", required=True, help="Path to instances JSON file")
    parser.add_argument("--log_path", required=True, help="Path to the log directory")
    parser.add_argument("--patches_path", required=True, help="Path to the patches directory")
    parser.add_argument("--output_path", required=True, help="Path to the output directory")
    parser.add_argument("--namespace", help="Docker namespace")
    args = parser.parse_args()

    if not os.path.exists(args.log_path):
        os.makedirs(args.log_path)
    if not os.path.exists(args.patches_path):
        os.makedirs(args.patches_path)
    if not os.path.exists(args.output_path):
        os.makedirs(args.output_path)
    
    begin = datetime.now()
    datetime_str_begin = begin.strftime('%Y %m %d %H %M %S')
    print(f"#### start time: {datetime_str_begin}")

    main(args)

    end = datetime.now()
    datetime_str_end = end.strftime('%Y %m %d %H %M %S')
    print(f"#### end time: {datetime_str_end}")