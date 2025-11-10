from agents.agent import CodeAgent
from utils.llm import get_llm_response
from utils.sandbox import Sandbox
from utils.agent_util import *
from agents.reproduce_prompt import *
from itertools import groupby
import json

def merge_snippets(snippet_list):
    sorted_snippets = sorted(snippet_list, key=lambda x: (x['file_path'], x['start_line']))

    merged_snippets = []
    for file_path, group in groupby(sorted_snippets, key=lambda x: x['file_path']):
        
        group = list(group) 
        current_merged = group[0]
        for snippet in group[1:]:
            if snippet['start_line'] <= current_merged['end_line'] + 1:
                current_merged['end_line'] = max(current_merged['end_line'], snippet['end_line'])
            else:
                merged_snippets.append(current_merged)
                current_merged = snippet
        
        merged_snippets.append(current_merged)
    
    print("Unmerged code snippet:")
    for snippet in snippet_list:
        print(snippet)
    print("Merged code snippet:")
    for snippet in merged_snippets:
        print(snippet)
    return merged_snippets

class Reproducer(CodeAgent):
    def __init__(self, sandbox):
        self.model = "gpt-4o-2024-05-13"
        self.max_turn = 30
        self.sandbox = sandbox
        self.sandbox_session = self.sandbox.get_session()
        self.edit_number = 3
        self.edit_time = 5
        self.reproduce_file_path = ''
        self.reproduce_contents = []

    def run(self, project_path, issue, trajectory, related_code = False, instance_id = None):

        def reproduce_context():
            self.messages = []
            system_message = {"role": "user", "content": context_prompt_init + context_prompt_reproduce}
            self.messages.append(system_message)
            searcher_message = {"role": "user", "content": f"[Project root path]: \n{project_path}\n [Issue statement]: We're currently solving the following issue within the project. The project has been installed in edit mode, do not install it repeatedly. Here's the issue text:\n{issue}\n"}
            self.messages.append(searcher_message)
            turn = 0
            while(turn < self.max_turn):
                turn += 1
                searcher_answer_list, usage = get_llm_response(self.model, self.messages)
                searcher_answer = searcher_answer_list[0]
                assistant_message = {"role": "assistant", "content": searcher_answer}
                self.messages.append(assistant_message)
                print(searcher_answer)
                system_res = ''
                code_snippets = extract_codes(searcher_answer)
                
                if code_snippets == None: 
                    commands = extract_commands(searcher_answer)
                    if (len(commands) != 0):
                        for i in range(len(commands)):
                            sandbox_res =  self.sandbox_session.execute(commands[i])
                            system_res += sandbox_res
                            if TIME_OUT_LABEL in sandbox_res:
                                self.sandbox_session =  self.sandbox.get_session()
                    else:
                        system_res += "### Observation: Fail to extract valid action or answer in your reply. Please include commands in ``` bash``` block or provide formatted answer with related code snippets."
                else:
                    break

                print(system_res)
                system_res += f"\nENVIRONMENT REMINDER: You have {self.max_turn - turn} turns left to complete the code search task."
                system_message = {"role": "user", "content": system_res}
                self.messages.append(system_message)
            
            # 兜底策略
            turn_temp = 0
            turn_max_temp = 10
            merged_snippets = None
            context = ''
            explain = ''

            if code_snippets:
                merged_snippets = merge_snippets(code_snippets)
                explain = extract_explain(searcher_answer)

                if explain and merged_snippets:
                    for snippet in merged_snippets:
                        cmd = f'review_file -f {snippet["file_path"]} -s {snippet["start_line"]} -e {snippet["end_line"]} --line_limit'
                        context += self.sandbox_session.execute(cmd) + '\n'
                else:
                    code_snippets = None
            if code_snippets == None:
                while(turn_temp < turn_max_temp):
                    turn_temp += 1
    
                    system_message = {"role": "system", "content": context_prompt_last}
                    self.messages.append(system_message)
                    searcher_answer_list, usage = get_llm_response(self.model, self.messages)
                    searcher_answer = searcher_answer_list[0]
                    code_snippets = extract_codes(searcher_answer)

                    if code_snippets:
                        merged_snippets = merge_snippets(code_snippets)
                        explain = extract_explain(searcher_answer)
                        if merged_snippets and explain:
                            for snippet in merged_snippets:
                                cmd = f'review_file -f {snippet["file_path"]} -s {snippet["start_line"]} -e {snippet["end_line"]} --line_limit'
                                context += self.sandbox_session.execute(cmd) + '\n'
                                if TIME_OUT_LABEL in context:
                                    self.sandbox_session =  self.sandbox.get_session()
                            break
            
            append_trajectory(trajectory, self.messages,'reproducer_context')
            good_context = get_good_context(issue, context, explain)
            if context == '':
                print("context is None!\n")
            if explain == '':
                print("explain is None!\n")

            print("good context begin: \n")
            print(good_context)
            print("good context end: \n")

            return good_context
            
        def reproduce_judger(good_reproduce_content, good_reproduce_content_output):
            self.messages = []
            context = get_judge_good_context(good_reproduce_content, good_reproduce_content_output) 
            user_message = {"role": "user", "content": judge_good_prompt_init + f"Here's the issue text:\n{issue}\n" + context}
            self.messages.append(user_message)
            answer_list, usage = get_llm_response(self.model, self.messages)
            answer = answer_list[0]
            assistant_message = {"role": "assistant", "content": answer}
            self.messages.append(assistant_message)
            result = extract_result(answer)
            explain = extract_explain(answer)
            print('reproduce to judge-', good_reproduce_content_output)
            print('reproduce judge-', explain)

            # 查找所有匹配的文件名
            while not result or not explain:
                system_message = {"role": "user", "content": judge_good_prompt_last}
                self.messages.append(system_message)
                answer_list, usage = get_llm_response(self.model, self.messages)
                answer = answer_list[0]
                assistant_message = {"role": "assistant", "content": answer}
                self.messages.append(assistant_message)
                result = extract_result(answer)
                explain = extract_explain(answer)
                
            if result == RESULT.SUCCEED:
                return True, explain
            if result == RESULT.FAILED:
                return False, explain
    
        def reproduce_edit(good_context):
            
            def provide_environment_feedback(state):
                feedback = {
                    "Create": "### Observation: The initial script creation is complete. The next state is ### State: Execute. Required action: Execute the script to obtain execution information.",
                    "Execute": "### Observation: The script execution is complete. The next state is ### State: Self-Verify. Required action: Verify the execution information to determine if it accurately reflects the bug.",
                    "Self-Verify": "### Observation: The self-verification of the script is complete. If the bug is accurately reflected, the next state is ### State: External-Verify. Required action: Send the script for external verification. If the bug is not accurately reflected, the next state is ### State: Modify. Required action: Explain the reasons for bug reproduction failure and modify the script.",
                    "External-Verify": "### Observation: The external verification of the script is complete. If the external verification confirms the issue, the next state is ### State: Report. Required action: Submit the generated bug reproduction script and report success by outputing ### Result: succeed. If the external verification fails, the next state is ### State: Modify. Required action: Explain the reasons for bug reproduction failure and modify the script.",
                    "Modify": "### Observation: The script modification is complete. The next state is ### State: Execute. Required action: Re-execute the modified script to obtain new execution information.",
                    "Report": "### Observation: The bug reproduction script has been successfully generated and reported. No further action required.",
                }

                return feedback.get(state, "### Observation: Unknown state. No action available for this state.")
            
            temperature = 0.7
            self.reproduce_file_path = f"{project_path}/reproduce.py"
            self.sandbox_session.execute(f"reset_repository -p {project_path}")

            self.messages = []
            system_message = {"role": "system", "content": edit_prompt_init + edit_prompt_reproduce}
            self.messages.append(system_message)
            content = f"The following are the issue description, related buggy code, unit tests and other information: {good_context}" + f"[Project root path]: \n{project_path}\n [Problem statement]: We're currently solving the following issue within our project. The project has been installed in edit mode, do not install it repeatedly."
            user_message = {"role": "user", "content": content}
            self.messages.append(user_message)
            
            content = 'The following failed reproduce.py is written by your colleagues.'
            if self.reproduce_contents:
                for reproduce_content_bad in self.reproduce_contents:
                    content += f"However this reproduce.py does not reproduce the issue successfully after repeated modifications because of the reasons below:\n {reproduce_content_bad['reproduce_thought']} \n. Please be careful not to write reproduce.py like this again. The file content is: \n {reproduce_content_bad['reproduce_content']} \n"
                system_message = {"role": "system", "content": content}
                self.messages.append(system_message)

            turn = 0
            edit_time = 0
            while(turn < self.max_turn):
                print('*********************')
                turn += 1
                reproducer_answer_list, usage = get_llm_response(self.model, self.messages, temperature)
                reproducer_answer = reproducer_answer_list[0]
                print(reproducer_answer)
                assistant_message = {"role": "assistant", "content": reproducer_answer}
                self.messages.append(assistant_message)
                result = extract_result(reproducer_answer)
                thought = extract_thought(reproducer_answer)
                commands = extract_commands(reproducer_answer)
                diffs = extract_diffs(reproducer_answer)
                state = extract_states(reproducer_answer)
                environment_feedback = provide_environment_feedback(state)
                num_of_action = reproducer_answer.count("### Action")
                system_res = ''

                if result and (commands or diffs):
                    system_res += f"### Observation: ERROR! Your reply contains both the final report and intermediate action, which is not acceptable. Please submit the final report only after you have completed your tasks."
                elif result != None:
                    final_answer = reproducer_answer
                    reproduce_content1 = self.sandbox.container.exec_run(f"cat {self.reproduce_file_path}").output.decode()
                    if result == RESULT.SUCCEED:
                        self.reproduce_contents.append({'reproduce_state':'double', 'reproduce_content':reproduce_content1, 'reproduce_thought': thought})
                        append_trajectory(trajectory, self.messages, 'reproducer')
                        return reproduce_content1
                    if result == RESULT.FAILED:
                        self.reproduce_contents.append({'reproduce_state':'bad', 'reproduce_content':reproduce_content1, 'reproduce_thought': thought})
                        append_trajectory(trajectory, self.messages, 'reproducer')
                        return None
                    break
                elif num_of_action > 1:
                    system_res += '''
### Observation:
Error! Each answser should only contain one pair of ###Thought and ###Action. Please resubmit your answer!
Please submit the first command first, then after receiving the response, you can issue the second command. 
You are free to use any other bash communication. Each round of your answers contain only *ONE* action!
'''
                elif len(diffs) != 0 and len(commands) != 0:
                    system_res += f"### Observation: ERROR! Your reply contains both bash block and diff block, which is not accepted. Each round of your reply can only contain one {BASH_FENCE[0]} {BASH_FENCE[1]} block or one {DIFF_FENCE[0]} {DIFF_FENCE[1]} block. Each round of your answers contain only *ONE* action!"
                elif len(commands) != 0: 
                    sandbox_res = ''
                    for i in range(len(commands)):
                        if 'self_verify' in commands[i]:
                            system_res += environment_feedback
                            continue
                        if 'external_verify' in commands[i]:
                            system_res += environment_feedback
                            reproduce_content = self.sandbox.container.exec_run(f"cat {self.reproduce_file_path}").output.decode()
                            reproduce_output = self.sandbox.container.exec_run(f"python3 {self.reproduce_file_path}").output.decode()

                            judge, thought = reproduce_judger(reproduce_content, reproduce_output)
                            if judge:
                                system_res += thought
                            else:
                                system_res += thought 
                                self.reproduce_contents.append({'reproduce_state':'single','reproduce_content':reproduce_content, 'reproduce_thought': thought})
                        else:
                            if 'reproduce.py' not in commands[i] or 'python' not in commands[i]:
                                system_res += f"### Observation: You can only edit and run the reproduce.py. Other commands are prohibited from being executed! ####"
                            
                            if 'python' in commands[i] and 'reproduce.py' in commands[i]:
                                sandbox_res += self.sandbox_session.execute(commands[i])
                                sandbox_res += environment_feedback
                                system_res += sandbox_res

                            if TIME_OUT_LABEL in sandbox_res:
                                self.sandbox_session =  self.sandbox.get_session()

                            # 有python肯定是运行reproduce.py，检查是否报错
                            if 'python' in commands[i] and 'reproduce.py' in commands[i]:
                                if 'Error' not in sandbox_res:
                                    reproduce_content1 = self.sandbox.container.exec_run(f"cat {self.reproduce_file_path}").output.decode()
                                    system_res += f"### Observation: The reproduce.py you create does not fail before the issue is resolved. You should modify the reproduce.py to fulfill the following conditions:{conditions} ####"
                                    system_res += f"### Observation: The content of reproduce.py is: \n {reproduce_content1} \n ####"

                elif len(diffs) != 0:
                    sandbox_res = ''
                    reproduce_file_path_tmp = diffs.split('\n')[1]
                    if 'reproduce.py' in reproduce_file_path_tmp and reproduce_file_path_tmp != self.reproduce_file_path:
                        self.reproduce_file_path = reproduce_file_path_tmp
 
                    if edit_time > self.edit_time:
                        system_res += f"Maximum number of edits"
                        break

                    tmp_name = save_diff_description(diffs)
                    if 'reproduce.py' not in diffs:
                        system_res += f"### Observation: You can only create and edit reproduce.py. Other files are prohibited from being created and edited! The reproduce file must be located in project root and name as 'reproduce.py'.####"

                    if 'reproduce.py' in diffs:
                        sandbox_res +=  self.sandbox_session.edit(tmp_name, project_path)
                        sandbox_res += environment_feedback
                        edit_time += 1
                        system_res += sandbox_res

                    if TIME_OUT_LABEL in sandbox_res:
                        self.sandbox_session =  self.sandbox.get_session()
                    
                    if HEAD not in diffs:
                        system_res += f"### Observation: Your patch is incomplete with {HEAD} missing! ####"
                        
                    reproduce_content1 = self.sandbox.container.exec_run(f"cat {self.reproduce_file_path}").output.decode()

                    if HEAD not in diffs:   
                        if 'No such file or directory' not in reproduce_content1:
                            system_res += f"### Observation: The content of reproduce.py is {reproduce_content1} ####"
                        else:
                            system_res += f"### Observation: The content of reproduce.py is empty now. ####"

                else:
                    system_res += "### Observation: ERROR! Your reply does not contain valid block or final answer."
                system_res += f"\nENVIRONMENT REMINDER: You have {self.max_turn - turn} turns left to complete the task."
                print(system_res)
                system_response = {"role": "user", "content": system_res}
                self.messages.append(system_response)
        
            append_trajectory(trajectory, self.messages, 'reproducer')

            reproduce_content1 = self.sandbox.container.exec_run(f"cat {self.reproduce_file_path}").output.decode()
            print(f"last reproduce content begin: \n")
            print(reproduce_content1)
            self.reproduce_contents.append({'reproduce_state':'last', 'reproduce_content':reproduce_content1, 'reproduce_thought': thought})
            print(f"last reproduce content end: \n")
            if TIME_OUT_LABEL in sandbox_res:
                self.sandbox_session =  self.sandbox.get_session()

            return None
        
        # module1
        good_context = reproduce_context()

        # module2
        for index in range(self.edit_number):
            self.sandbox.container.exec_run(f"rm {self.reproduce_file_path}")
            good_reproduce_content = reproduce_edit(good_context)
            if good_reproduce_content:
                break

        selected_reproduce_content = ''
        flag = ''
        for reproduce_content in self.reproduce_contents:
            if reproduce_content['reproduce_state'] == 'double':
                selected_reproduce_content = reproduce_content['reproduce_content']
                break
            if reproduce_content['reproduce_state'] == 'single':
                flag = 'single'
                selected_reproduce_content = reproduce_content['reproduce_content']
            if reproduce_content['reproduce_state'] == 'last':
                if flag != 'single':  
                    selected_reproduce_content = reproduce_content['reproduce_content']
            
        # 重置仓库代码
        print(f"AEGIS reproduce content begin: \n")
        print(selected_reproduce_content)
        print(f"AEGIS reproduce content end: \n")

        print(f"AEGIS reproduce file path begin: \n")
        print(self.reproduce_file_path)
        print(f"AEGIS reproduce file path end: \n")
        self.sandbox_session.execute(f"git reset --hard HEAD && rm {self.reproduce_file_path}")
 
        self.sandbox_session.close()
        return trajectory, selected_reproduce_content