import json, yaml, os, sys, shutil, time
import logging, traceback, time, base64
import tarfile, re

from . import executor, func

class CompileResult:
    def __init__(self, exe_time, exit_code, compiler_output, compile_result, log, success):
        # 编译用时，编译器返回值，编译器输出
        self.exe_time = exe_time
        self.exit_code = exit_code
        self.compiler_output = compiler_output
        self.compile_result = compile_result
        self.log = log
        self.success = success
        self.executable = None
        self.execute_cmd = None

class ExecuteCommand:
    def __init__(self, source, executable, compile_cmd, execute_cmd):
        self.source = source
        self.executable = executable
        self.compile = compile_cmd
        self.execute = execute_cmd

def get_execute_command(language, source_file, path, request_name=False):
    run_cmd_dict = {}
    with open(source_file, 'r') as src_fp:
        source = src_fp.read()
    if language.get('variable', None) != None:
        for var in language['variable']:
            _name = var['name']
            if var['type'] == 'regexp':
                _res = re.search(var['value'], source).group(int(var['match']))
            elif var['type'] == 'string':
                _res = var['value']
            run_cmd_dict[_name] = _res
    # 处理source和executable这两个变量
    if not request_name:
        filename = source_file
    else:
        filename = os.path.join(path, language['default'])
    run_cmd_dict['filename'] = filename
    source = language.get('source', '{filename}')
    executable = language.get('executable', '{filename}.exe')
    source = source.format(**run_cmd_dict)
    executable = executable.format(**run_cmd_dict)
    run_cmd_dict['source'] = source
    run_cmd_dict['executable'] = executable
    # 最后处理编译和运行的参数
    compile_cmd = func.format_list(language['compile']['args'], run_cmd_dict)
    execute_cmd = func.format_list(language['execute']['cmd'], run_cmd_dict)
    return ExecuteCommand(source, executable, compile_cmd, execute_cmd)

def compile(language, working_dir, code, executable=None):
    # 对于部分语言，编译这个过程可能要在源代码的文件夹中进行
    # 比如golang，虽然也可以不用
    # language: 语言的配置文件
    # working_dir: 编译目录
    # code: 源代码文件名，相对于当前目录
    # target: 编译出来的目标
    # 输出：CompileResult
    curdir = os.getcwd()
    os.chdir(os.path.dirname(os.path.join(working_dir, code)))
    compile_args = get_execute_command(language, os.path.join(working_dir, code), working_dir)
    compile_cmd = compile_args.compile
    compile_output = open('compiler_error', 'w')
    # 正式编译
    compile_start = time.time()
    compile_res = executor.execute(cmd=compile_cmd, timelimit=language['compile']['timelimit'], stdout=compile_output, stderr=compile_output)
    compile_output.close()
    compile_time = time.time() - compile_start
    # 整理结果
    compile_stdout = ""
    with open("compiler_error", "r") as compile_stdout:
        compile_stdout = compile_stdout.read(8192)
    os.chdir(curdir)
    return CompileResult(compile_res[2], compile_res[3], compile_stdout, compile_args.executable, compile_res[4], compile_res[3] == 0)
