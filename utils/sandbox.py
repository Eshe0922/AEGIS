# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Xinchen Wang 王欣辰

import docker
import pexpect
import time 
import subprocess
import os 
import glob


class Sandbox:
    def __init__(self, namespace, instance):
        self.namespace = namespace
        self.client = docker.from_env()
        self.container = None
        self.shell = None
        # self.commit_id = instance["base_commit"]
        self.instance_id = instance["instance_id"]

    def get_project_path(self):
        project_path = self.container.exec_run("pwd").output.decode().strip()
        return project_path

    def start_container_build(self):
        image = self.namespace
        self.container = self.client.containers.run(image, detach=True, tty=True, stdin_open=True, privileged=True)
        current_file_path = os.path.abspath(__file__)
        current_directory = os.path.dirname(current_file_path)
        project_directory = os.path.dirname(current_directory)

        cmd = f"chmod -R 777 {project_directory}/tools && docker cp {project_directory}/tools {self.container.name}:/home/swe-bench"
        subprocess.run(cmd, check=True, shell=True)
        print(f"Container {self.container.short_id} started with image {image}")

    def start_container(self):
        image = self.namespace
        host_path = '/tmp/patch'
        container_path = '/tmp/patch'

        cmd = f"sudo chmod -R 777 {host_path}"
        subprocess.run(cmd, check=True, shell=True)
        
        self.container = self.client.containers.run(
            image, 
            detach=True, 
            tty=True, 
            stdin_open=True, 
            privileged=True,
            volumes={host_path: {'bind': container_path, 'mode': 'rw'}}
            )
        print(f"Container {self.container.short_id} started with image {image}")
        
        current_file_path = os.path.abspath(__file__)
        current_directory = os.path.dirname(current_file_path)
        project_directory = os.path.dirname(current_directory)
        
        cmd = f"chmod -R 777 {project_directory}/tools && docker cp {project_directory}/tools {self.container.name}:/home/swe-bench"
        subprocess.run(cmd, check=True, shell=True)

        checkout_res = self.container.exec_run(f"git checkout {self.commit_id}")
        print('checkout: ',checkout_res)

    def get_diff_result(self, project_path: str):
        max_retries = 3
        retries = 0
    
        while retries < max_retries:
            try:
                res = self.container.exec_run(f"python3 /home/swe-bench/tools/get_diff.py -p {project_path}").output.decode()
                return res
            except Exception as e:
                print(f"Attempt {retries + 1}: An error occurred while executing the command - {e}")
                time.sleep(5)
                retries += 1
    
        print(f"Failed to execute the command after {max_retries} attempts.")
        return ''

    def start_shell(self):
        if self.container:
            if self.shell and self.shell.isalive():
                self.shell.close(force=True)  
            command = f'docker exec -it {self.container.id} /bin/bash'
            self.shell = pexpect.spawn(command)
            self.shell.expect([r'\$ ', r'# '], timeout=10)  
        else:
            raise Exception("Container not started. Call start_container() first.")
        
    def get_session(self):
        self.start_shell()

        class Session:
            def __init__(self, sandbox):
                self.sandbox = sandbox

            def execute(self, command, timeout=60):
                try:
                    if command[-1] != '&':
                        self.sandbox.shell.sendline(command + "&& sleep 0.5")
                    else:
                        self.sandbox.shell.sendline(command)
                    self.sandbox.shell.expect([r'swe-bench@.*:.*\$ ', r'root@.*:.*# '], timeout=timeout)

                    output = self.sandbox.shell.before.decode('utf-8').strip()
                    output_lines = output.split('\r\n')
                    if len(output_lines) > 1:
                        output_lines = output_lines[1:-1]  
                   
                    result_message = '###Observesion: ' + '\n'.join(output_lines)
                    return result_message
                
                except pexpect.TIMEOUT:
                    partial_output = self.sandbox.shell.before.decode('utf-8').strip()
                    partial_output_lines = partial_output.split('\n')
                    if len(partial_output_lines) > 1:
                        partial_output_lines = partial_output_lines[1:-1]
                    partial_output = '\n'.join(partial_output_lines)
                    return '### Observesion: ' + f"Error: Command '{command}' timed out after {timeout} seconds. Partial output:\n + {partial_output}"
        
            def edit(self, edit_tmp_file:str, project_path:str, timeout=60):
                command = f"python3 /home/swe-bench/tools/code_edit.py -f '{edit_tmp_file}' -p '{project_path}'"
                try:
                    self.sandbox.shell.sendline(command)
                    self.sandbox.shell.expect([r'swe-bench@.*:.*\$ ', r'root@.*:.*# '], timeout=timeout) 
                    output = self.sandbox.shell.before.decode('utf-8').strip()
                    output_lines = output.split('\r\n')
                    if len(output_lines) > 1:
                        output_lines = output_lines[1:-1]  
                
                    return '### Observesion: ' + '\n'.join(output_lines)

                except pexpect.TIMEOUT:
                    return '### Observesion: ' + f"Error: Edit timed out after {timeout} seconds."
                
            def close(self):
                if self.sandbox.shell:
                    self.sandbox.shell.sendline('exit')
                    self.sandbox.shell.expect(pexpect.EOF)
                    self.sandbox.shell.close(force=True)
                    self.sandbox.shell = None  

        return Session(self)

    def stop_container(self):
        if self.container:
            if self.shell and self.shell.isalive():
                self.shell.close(force=True)  
                self.shell = None
            self.container.stop()
            self.container.remove()
            print(f"Container {self.container.short_id} stopped and removed")
            self.container = None


if __name__ == "__main__":
    sandbox = Sandbox("pyairbyte", {"base_commit":1, "instance_id":1})
    sandbox.start_container_build()
