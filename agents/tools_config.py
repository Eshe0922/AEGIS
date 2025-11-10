# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Xinchen Wang 王欣辰

from enum import Enum
class Tools(Enum):
    search_entity_in_project = {
        "command": "search_entity_in_project -e 'entity_name' -p 'project_root_path'",
        "description": "Search the implementation location of an entity within the project scope. You need to provide the complete and exactly entity name for searching like 'BuildPy', 'update_matplotlibrc' ... Entities contain functions and classes. Highly recommended!"
    }
    search_class_in_project = {
        "command": "search_class_in_project -c 'class_name' -p 'project_root_path'",
        "description": "Search the implementation location of a class within the project scope. You need to provide the complete and exactly class name for searching. Highly recommended!"
    }
    search_function_in_project = {
        "command": "search_function_in_project -f 'function_name' -p 'project_root_path'",
        "description": "Search the implementation location of a function within the project scope. You need to provide the complete and exactly function name for searching. Highly recommended!"
    }
    search_file_in_project = {
        "command": "search_file_in_project -f 'file_name'  -p 'path'",
        "description": "Search the file within the project scope. You need to provide the complete and exactly file name with suffix for searching like 'test_metric.cpp', 'setup.py'... Recommended!"
    }
    search_identifier_in_file = {
        "command": "search_identifier_in_file -f 'file_path' -i 'identifier'",
        "description": "search where an identifier occurs in the file. file_path is the complete absolute path of the file. Recommended when you can not find entity by search_entity!"
    }
    review_definition = {
        "command": "review_definition -f 'file_path' -p 'project_path' -l lineno -i 'identifier'",
        "description": "View the definition according to identifier name and position. Powered by launguage server protocal, Highly recommended!"
    }
    search_code_in_project = {
        "command": "search_snippet_in_project -s 'code snippet' -p 'project_root_path'",
        "description": "Search the relevate code snippet within the project scope. You need to provide the code snippet for searching."
    }
    ls = {
        "command": "ls 'project_path'",
        "description": "Query the files under the project path. Recommended!"
    }
    review_file = {
        "command": "review_file -f 'file_path' -s start_lineno -e end_lineno",
        "description": "View the file content between [start_lineno] and [end_lineno] in file. Each call can browse up to 100 lines of content. file_path is the complete absolute path of the file. Do not use this tool to find the code line by line! it is very inefficient. Not recommended if you do not know the exact location of the target code"
    }
    reset_repository = {
        "command": "reset_repository -p 'project_path'",
        "description": "Abandon all changes and reset the code repository to base commit state. project_path must be the project root directory"
    }
    run_produce = {
        "command": "python3 /.../reproduce.py",
        "description": "Run the reproduce.py to verify that the reproduce was successful."
    }