from utils.agent_util import BASH_FENCE, DIFF_FENCE, HEAD, DIVIDER, UPDATED
from agents.tools_config import Tools

tool_lib_context = [
    Tools.search_class_in_project, 
    Tools.search_function_in_project,
    Tools.search_file_in_project,
    Tools.search_identifier_in_file,
    Tools.ls,
    Tools.review_file,
    Tools.review_definition,
    # Tools.reset_repository,
    # Tools.run_produce
]
tools_list_context = ""
for tool in tool_lib_context:
    tools_list_context += f"{tool.value['command']} # {tool.value['description']}\n"


conditions = f"""
Now, you are going to create unit tests that cover the issue. 
1. You should write unit tests that fail (throw errors) in the current state of the repository but will pass when the issue has been resolved. 
2. To show the written unit tests fail in the current repository, we recommend using `raise AssertionError(e)` instead of a `print("Test failed as expected with error:", e)` command.
3. To show the written unit tests pass when the issue has been resolved, we recommend adding a `print("Test passed successfully with no errors!")` command.
4. Note that you are not trying to solve the bug itself, but just capture the behavior described in the issue by creating appropriate tests.
"""

context_prompt_init = f"""\
Act as a helpful assistant tasked with searching buggy code and unit tests related to the issue.

IN GOOD FORMAT:
Calling CLI tools Action using bash block like {BASH_FENCE[0]}  {BASH_FENCE[1]}. 

CLI TOOLS: 
You can use the following tools listed below to search buggy code and unit tests:
{tools_list_context}

A reference format is as follows: 
### Thought: I need to search the function test_power_a in repo.
### Action:
{BASH_FENCE[0]} 
search_function_in_project -f 'test_power_a' -p '/home/swebench/test_repo'
{BASH_FENCE[1]}

IMPORTANT TIPS: 
* You need to keep collecting code snippets until all relevant code snippets are collected.
* Each code snippet you provide should be a complete class or function. 
* You are only responsible for search code need to edit, and other work is done by your colleagues.
* Please submit the first command first, then after receiving the response, you can issue the second command. You are free to use any other bash communication. Each round of your answers contain only *ONE* action!
"""

context_prompt_reproduce = f"""\
You should strictly follow the work process step by step.

[Step 1: Locate Relevant Buggy Code] Identify files and code snippets related to the issue description within the project repository.

A reference format is as follows: 
### Thought: I need to locate the function func_a in repo. This information is relavant to the issue, because the 'func_a' is mentioned in the issue.
### Action:
{BASH_FENCE[0]} 
search_function_in_project -f 'func_a' -p '/home/swebench/repo'
{BASH_FENCE[1]}

[Step 2: Locate Relevant Unit Tests] Review unit tests related to the issue within the repository. 

A reference format is as follows: 
### Thought: I will review the `repo/tests/test_func.py` because it already contains a test function `test_func_a` related to the issue.
### Action:
{BASH_FENCE[0]} 
review_file -f 'repo/tests/test_func.py' -s 120 -e 160
{BASH_FENCE[1]}

[Step 3: Return the final report]

FINAL REPORT: Your final answer must follow the following format:

### Result: 
/abs/path/to/fileA 11~80
/abs/path/to/fileA 90~120

### Explanation: 
I have retrieved all the buggy code and unit tests related to the issue and I have totally understood the issue description and checked the reproduction method in the issue description. 
1. Buggy Code Relevance: The [Specific Buggy Code XXX, citing from the specific buggy code in the retrieved context] is related to the issue, because [Point-by-point, detailed reasons, elaborating on how the buggy code contributes to or causes the issue].
2. Unit Tests Relevance: The [Specific Unit Test XXX, citing from the specific unit test in the retrieved context] is related to the issue, because [Point-by-point, detailed reasons, explaining how the tests are designed to detect or address the issue].
3. Reproduction Method Analysis: The Issue Description does not contains the reproduction method to reproduce the issue. / The Issue Description contains the reproduction method to reproduce the issue and the exact code of the reproduction method is [exact reproduction method code citing from the issue description].
4. Expected Result Analysis: The expected result is ... once the issue is resolved, but the current result is .... due to the issue. 

IMPORTANT TIPS: 
* You must provide the full absolute path of the file where the code snippet is located.
* In the result, each code snippet must be a separate line.
* Your results should include the files, starting and ending lines of all relevant code snippets.
* In the explanation, you should check and understand the reproduction method in the issue description. If the Issue Description contains the reproduction method, you must provide the exact code of the reproduction method!!!
* In the explanation, you should explain the detailed relevance of the buggy code and unit test to the issue.   
"""

context_prompt_last = f"""\
You've run out of turns to retrieve buggy code and unit tests related to the issue, now you have to return the final report according to the retrieved context!!!

FINAL REPORT: Your final answer must follow the following format:

### Result: 
/abs/path/to/fileA 11~80
/abs/path/to/fileA 90~120

### Explanation: 
I have retrieved all the buggy code and unit tests related to the issue and I have totally understood the issue description and checked the reproduction method in the issue description. 
1. Buggy Code Relevance: The [Specific Buggy Code XXX, citing from the specific buggy code in the retrieved context] is related to the issue, because [Point-by-point, detailed reasons, elaborating on how the buggy code contributes to or causes the issue].
2. Unit Tests Relevance: The [Specific Unit Test XXX, citing from the specific unit test in the retrieved context] is related to the issue, because [Point-by-point, detailed reasons, explaining how the tests are designed to detect or address the issue].
3. Reproduction Method Analysis: The Issue Description does not contains the reproduction method to reproduce the issue. / The Issue Description contains the reproduction method to reproduce the issue and the exact code of the reproduction method is [Exact Reproduction Method Code citing from the issue description].
4. Expected Result Analysis: The expected result is ... once the issue is resolved, but the current result is .... due to the issue.  

IMPORTANT TIPS: 
* You must provide the full absolute path of the file where the code snippet is located.
* In the result, each code snippet must be a separate line.
* Your results should include the files, starting and ending lines of all relevant code snippets.
* In the explanation, you should check and undetstand the reproduction method in the issue description. If the Issue Description contains the reproduction method, you must provide the exact code of the reproduction method!!!
* In the explanation, you should explain the detailed relevance of the buggy code and unit test to the issue.      
"""


tool_lib_edit = [
    # Tools.reset_repository,
    Tools.run_produce
]
tools_list_edit = ""
for tool in tool_lib_edit:
    tools_list_edit += f"{tool.value['command']} # {tool.value['description']}\n"


edit_prompt_init = f""" \
Act as a helpful assistant tasked with writing tests to reproduce the issue according to the issue description, buggy code and related unit tests.

IN GOOD FORMAT:
Calling CLI tools Action using bash block like {BASH_FENCE[0]}  {BASH_FENCE[1]}. 
Editing code Action using diff block like {DIFF_FENCE[0]} {DIFF_FENCE[1]}.

CLI TOOLS: 
You can use the following tools listed below to write tests:
{tools_list_edit}

CODE EDITING:
All changes to files must use the {DIFF_FENCE[0]} {DIFF_FENCE[1]} format.
If you want write code, you need to provide code patch. The patch should according to the original code, indent correctly, and do not include line numbers. The format is as follows: 
### Thought: Modify explanation...
### Action: 
{DIFF_FENCE[0]}
/absolute/path/of/reproduce.py
{HEAD}
    [exact copy of old line(s) you would like to change]
{DIVIDER}
    [new line(s) to replace]
{UPDATED}

{HEAD}
    [exact copy of old line(s) you would like to change, 3~20 lines recommend!]
{DIVIDER}
    [new line(s) to replace]
{UPDATED}
{DIFF_FENCE[1]}
Every *SEARCH/REPLACE block* must use this format:
1. The opening fence {DIFF_FENCE[0]}
2. The file path alone on a line, verbatim. No bold asterisks, no quotes around it, no escaping of characters, etc.
3. The start of search block: {HEAD}
4. A contiguous chunk of lines to search for in the existing source code
5. The dividing line: {DIVIDER}
6. The lines to replace into the source code
7. The end of the replace block: {UPDATED}
8. The closing fence: {DIFF_FENCE[1]}
Once you want to modify the code you MUST: 
    * Include *ALL* the code being searched and replaced!
    * Every *SEARCH* section must *EXACTLY MATCH* the existing source code, character for character, including all comments, docstrings, etc.
    * '{HEAD}', '{DIVIDER}' and  '{UPDATED}' symbols must be on a line by themselves and cannot be indented.
    * All code modifications must be expressed in the REPLACE format above (including delete an insert). We will find the source code with the highest matching degree in the original file and replace it. Please provide sufficient and unique old line(s) from snippet to facilitate matching.
    * If the code patch you provide is successfully applied, the differences before and after the code modification will be returned.
    * The paths of modified files must be completely absolute paths.
    * Make sure the patch you provide is indented correctly especially in python programs: The indentation of old lines is exactly the same as the original code, and the indentation of new lines is correct.
    * All patches must be based on the original code viewed by the tools, and fabricated code patch(es) is prohibited.
    * Previously successfully applied patches will modify the code, and new patches must be applied based on the current code. Please review the relevant code again then provide new patches.
    * If the old line is empty, it is considered to be inserted at the beginning of the file. If the file does not exist, a new file will be created and the new line will be written. like:
### Thought: Create reproduce.py
### Action:
{DIFF_FENCE[0]}
/project_path/.../reproduce.py
{HEAD}
{DIVIDER}
    [new line(s) to replace]
{UPDATED}
{DIFF_FENCE[1]}

IMPORTANT TIPS: 
    * Please submit the first command first, then after receiving the response, you can issue the second command. You are free to use any other bash communication.
    * You can only create reproduce.py, other files are prohibited from being created.
"""


edit_prompt_reproduce = f"""
You are a helpful assistant tasked with writing tests USING A NEWLY CREATED FILE NAMED `reproduce.py` to reproduce the issue according to the issue description, buggy code, and related unit tests.

You should strictly follow the conditions:
{conditions}

You should strictly follow the work process step by step:

[Step 1: Create] Create a reproduce.py according to the issue description, buggy code, and related unit tests.
A reference format is as follows: 
### Thought: I have gathered sufficient information and I will create the reproduce.py.
When running reproduce.py before the issue is resolved, the reproduce.py will fail because [Point-by-point, detailed reasons].
When running reproduce.py after the issue is resolved, the reproduce.py will pass because [Point-by-point, detailed reasons].
### State: Create
### Action:
{DIFF_FENCE[0]}
/absolute/path/of/reproduce.py
{HEAD}
{DIVIDER}
    [new line(s) to replace]
{UPDATED}
{DIFF_FENCE[1]}

Once you want to create the reproduce.py you MUST:
    * The format of the diff block must include {DIFF_FENCE[0]}, {HEAD}, {DIVIDER}, {UPDATED}, and {DIFF_FENCE[1]}.
    * You can only create reproduce.py, other files are prohibited from being created.
    * The reproduce file must be located in the project and named as 'reproduce.py'.
    * Your reproduce.py should function like a unit test.
    * You can only create reproduce.py, other files are prohibited from being created.

[Step 2: Execute] Execute the reproduce.py and obtain the execution information.
A reference format is as follows:  
### Thought: The `reproduce.py` file has been created successfully and I will run the reproduce.py.
### State: Execute
### Action:
{BASH_FENCE[0]}
python3 /absolute/path/of/reproduce.py
{BASH_FENCE[1]}

Once you want to run the reproduce.py you MUST:
    * You must run your reproduce.py file before returning 'succeed' result to verify that the issue has been successfully reproduced. Only creating a reproduce.py file does not mean that the reproduction is successful!

[Step 3: Self-Verify] Verify whether the reported error messages match the issue description.
A reference format is as follows:  
### Thought: I will verify whether the reported error messages match the issue description. I think ...
### State: Self-Verify
### Action:
{BASH_FENCE[0]}
self_verify
{BASH_FENCE[1]}

Important tips:
    If the `reproduce.py` does fail and the reported error messages match the issue description, go to [Step 4: External-Verify].
    If the `reproduce.py` does not fail or the reported error messages do not match the issue description, go to [Step 5: Modify reproduce.py].

[Step 4: External-Verify] An independent LLM agent will verify the reproduction script and its execution information.

A reference format is as follows:  
### Thought: The `reproduce.py` file has been validated internally and I will send it for external verification.
### State: External-Verify
### Action:
{BASH_FENCE[0]}
external_verify
{BASH_FENCE[1]}

Important tips:
    If the external verification confirms the issue has been successfully reproduced, go to [Step 6: Return the final report].
    If the external verification fails, go to [Step 5: Modify reproduce.py].

[Step 5: Modify] Modify the reproduce.py and go back to [Step 2: Run the reproduce.py]. 
    
A reference format is as follows: 
### Thought: The current `reproduce.py` does not fail (or the reported error messages do not match the issue description) and I will modify the reproduce.py.
### State: Modify
### Action:
{DIFF_FENCE[0]}
/absolute/path/of/reproduce.py
{HEAD}
    [exact copy of old line(s) you would like to change]
{DIVIDER}
    [new line(s) to replace]
{UPDATED}
{DIFF_FENCE[1]}

Once you want to modify the reproduce.py you MUST:
    * Give the old lines that need to be changed in the diff block, not empty.

[Step 6: Report]
If you have confirmed that the issue has been successfully reproduced or cannot be reproduced, return the final report. 
If you are able to reproduce the issue successfully, please provide the reproduce command and its expected output after the issue is resolved correctly in your explanation. 

A reference format is as follows: 
### Thought: I have successfully reproduced the issue. When running reproduce.py before the issue is resolved, the reproduce.py will fail because [Point-by-point, detailed reasons].
When running reproduce.py after the issue is resolved, the reproduce.py will pass because [Point-by-point, detailed reasons].
/ I cannot reproduce the issue ... 
### State: Report
### Result: succeed/failure


IMPORTANT TIPS: 
    * Each round of reply can only contain one {BASH_FENCE[0]} {BASH_FENCE[1]} block or one {DIFF_FENCE[0]} {DIFF_FENCE[1]} block, which means each round of your answers contains only *ONE* action!
    * You should first check whether the issue description contains a reproduction method. If it does, just follow the method.
    * Please submit the first command first, then after receiving the response, you can issue the second command. You are free to use any other bash communication.
    * If the issue statements suggest you add some test cases, please omit them!
    * Your job is to reproduce the bug described in the issue USING A NEWLY CREATED FILE NAMED `reproduce.py`. DO NOT EDIT THE CODE IN THE REPOSITORY!!!
    * YOU CAN USE ASSERT IN YOUR REPRODUCE. YOU CAN USE ASSERT IN YOUR REPRODUCE. YOU CAN USE ASSERT IN YOUR REPRODUCE.
    * YOU MUST FOLLOW THE CONDITIONS. YOU MUST FOLLOW THE CONDITIONS. YOU MUST FOLLOW THE CONDITIONS. 
"""



def get_good_context(issue, context, explain):
    good_context = f"""\
#### Issue Description #### 

{issue}

#### Buggy Code and Unit Tests related to the Issue ####

{context}

#### Explanation and Thought ####

{explain}     
    """
    return good_context


def get_judge_context(file_name, reproduce_content1, reproduce_content1_output, thought):
    judge_context = f"""\
######## TEST FILE NAME ########
{file_name}

######## TEST FILE CONTEXT ########
{reproduce_content1}

######## OUTPUT OF RUNNING THE TEST FILE  ########
{reproduce_content1_output}

######## REASON OF CONSTRUCTING THE TEST FILE  ########
{thought}
    """
    return judge_context


def get_judge_good_context(reproduce_content1, reproduce_content1_output):
    judge_context = f"""\
######## TEST FILE CONTEXT ########
{reproduce_content1}

######## OUTPUT OF RUNNING THE TEST FILE  ########
{reproduce_content1_output}

    """
    return judge_context

judge_prompt_init = f"""\

You are a helpful assistant responsible for determining which test file best reproduces the issue and the output of running the test file best matches the issue description.
You can only determine the only file that best meets the conditions above and give the only file name in the following fomat:
######## BEST FILE NAME ########
reproduce_idx.py  (the file name which best reproduces the issue) 

Each test file and the output of running the test file will be given in the following format:

######## TEST FILE NAME ########
reproduce_0.py

######## TEST FILE CONTEXT ########
from astropy.wcs import WCS

def test_wcs_pix2world_with_empty_lists():
    try:
        wcs = WCS('2MASS_h.fits')
        result = wcs.wcs_pix2world([], [], 0)
        assert result == ([], []), f"Expected ([], [])"
        print("Test passed successfully with no errors!")
    except Exception as e:
        raise AssertionError(e)

if __name__ == "__main__":
    test_wcs_pix2world_with_empty_lists()

######## OUTPUT OF RUNNING THE TEST FILE  ########
WARNING: The following header keyword is invalid or follows an unrecognized non-standard convention:
2MASS_h.fits                                                                     [astropy.io.fits.card]
Traceback (most recent call last):
  File "/home/swe-bench/astropy__astropy/reproduce_1.py", line 7, in test_wcs_empty_lists
    result = wcs.wcs_pix2world([], [], 0)
  File "/home/swe-bench/astropy__astropy/astropy/wcs/wcs.py", line 1352, in wcs_pix2world
    return self._array_converter(
  File "/home/swe-bench/astropy__astropy/astropy/wcs/wcs.py", line 1269, in _array_converter
    return _return_list_of_arrays(axes, origin)
  File "/home/swe-bench/astropy__astropy/astropy/wcs/wcs.py", line 1225, in _return_list_of_arrays
    output = func(xy, origin)
  File "/home/swe-bench/astropy__astropy/astropy/wcs/wcs.py", line 1353, in <lambda>
    lambda xy, o: self.wcs.p2s(xy, o)['world'],
astropy.wcs._wcs.InconsistentAxisTypesError: ERROR 4 in wcsp2s() at line 2647 of file cextern/wcslib/C/wcs.c:
ncoord and/or nelem inconsistent with the wcsprm.

######## REASON OF CONSTRUCTING THE TEST FILE  ########
When running `reproduce.py` before the issue is resolved, it will fail because:
1. The `wcs_pix2world` function does not handle empty lists or arrays and raises an `InconsistentAxisTypesError`.
2. The `_array_converter` helper function also does not account for empty inputs and attempts operations that lead to exceptions.

When running `reproduce.py` after the issue is resolved, it will pass because:
1. The `wcs_pix2world` function will correctly handle empty lists or arrays, returning empty outputs without raising exceptions.
2. The `_array_converter` helper function will be updated to manage empty inputs appropriately.
"""


judge_prompt_last = f"""\
The format of your answer is not correct!!!
The format of your answer is not correct!!!
The format of your answer is not correct!!!

You are a helpful assistant responsible for determining which test file best reproduces the issue and the output of running the test file best matches the issue description.
You can only determine the only file that best meets the conditions above and give the only file name in the following fomat:

######## BEST FILE NAME ########
reproduce_idx.py  (the file name which best reproduces the issue) 

"""

judge_good_prompt_init = f"""\

You are a helpful assistant responsible for judging whether the test file reproduces the issue successfully and the output of running the test file matches the issue description successfully.
Then you should give detailed reasons of your judegement.

Your final answer must follow the following format: 
### Result: succeed/failure
### Explanation: The test file reproduces the issue successfully because [Point-by-point, detailed reasons]. / The test file doesn't reproduce the issue successfully because [Point-by-point, detailed reasons].

The test file and the output of running the test file will be given in the following format:

######## TEST FILE CONTEXT ########
from astropy.wcs import WCS

def test_wcs_pix2world_with_empty_lists():
    try:
        wcs = WCS('2MASS_h.fits')
        result = wcs.wcs_pix2world([], [], 0)
        assert result == ([], []), f"Expected ([], [])"
        print("Test passed successfully with no errors!")
    except Exception as e:
        raise AssertionError(e)

if __name__ == "__main__":
    test_wcs_pix2world_with_empty_lists()

######## OUTPUT OF RUNNING THE TEST FILE  ########
WARNING: The following header keyword is invalid or follows an unrecognized non-standard convention:
2MASS_h.fits                                                                     [astropy.io.fits.card]
Traceback (most recent call last):
  File "/home/swe-bench/astropy__astropy/reproduce_1.py", line 7, in test_wcs_empty_lists
    result = wcs.wcs_pix2world([], [], 0)
  File "/home/swe-bench/astropy__astropy/astropy/wcs/wcs.py", line 1352, in wcs_pix2world
    return self._array_converter(
  File "/home/swe-bench/astropy__astropy/astropy/wcs/wcs.py", line 1269, in _array_converter
    return _return_list_of_arrays(axes, origin)
  File "/home/swe-bench/astropy__astropy/astropy/wcs/wcs.py", line 1225, in _return_list_of_arrays
    output = func(xy, origin)
  File "/home/swe-bench/astropy__astropy/astropy/wcs/wcs.py", line 1353, in <lambda>
    lambda xy, o: self.wcs.p2s(xy, o)['world'],
astropy.wcs._wcs.InconsistentAxisTypesError: ERROR 4 in wcsp2s() at line 2647 of file cextern/wcslib/C/wcs.c:
ncoord and/or nelem inconsistent with the wcsprm.
"""


judge_good_prompt_last = f"""\
The format of your answer is not correct!!!
The format of your answer is not correct!!!
The format of your answer is not correct!!!

You are a helpful assistant responsible for judging whether the test file reproduces the issue successfully and the output of running the test file matches the issue description successfully.
The you should give detailed reasons of your judegement.

Your final answer must follow the following format: 
### Result: succeed/failure
### Explanation:
The test file reproduces the issue successfully because [Point-by-point, detailed reasons]. / The test file doesn't reproduce the issue successfully because [Point-by-point, detailed reasons].

"""