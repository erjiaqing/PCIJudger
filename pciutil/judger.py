import requests, json, yaml, os, sys, shutil, time
import logging, traceback, time, base64, hashlib
import tarfile, re
import subprocess, traceback

from . import compiler, func, problem
from . import executor_lrun as executor_s
from . import executor as executor

class JudgeResult:
    def __init__(self, result, exe_time, exe_memory, exit_code, used_time, detail):
        self.success = True
        self.result = result
        self.exe_time = exe_time
        self.exe_memory = exe_memory
        self.exit_code = exit_code
        self.used_time = used_time
        self.detail = detail

def judge(conf, lang_file, code, problem):
    verdict = "SE"
    session_start = time.time()
    exe_time = 0.
    exe_memory = 0
    detail = []
    try:
        with open(lang_file, 'r') as lang_fp:
            lang = yaml.load(lang_fp)
        # 为Docker设计，不需要再创建临时目录
        working_dir = conf['tmp']
        os.chdir(workding_dir)
        # 计算编译和运行的参数
        full_args = compiler.get_execute_command(lang, code, os.getcwd(), True)
        # 写文件
        src_file = open(full_args.source, 'w')
        with open(code, 'r') as src:
            src_file.write(src.read())
        src_file.close()
        # 编译
        result = compiler.compile(lang, os.getcwd(), full_args.source)
        detail.append(dict(name="Compiler", output=result.compiler_output))
        if result.exit_code != 0:
            verdict = "CE"
            raise Exception("CE")
        # 评测
        with open(os.path.join(problem, "problem.yaml"), "r") as problem_yaml_fp:
            problem_yaml = yaml.load(problem_yaml_fp)
        time_limit = int(problem_yaml.get('time', 1000)) / 1000
        verdict = "AC"
        testid = 0
        for test in problem_yaml['case']:
            testid += 1
            this_detail = dict(name="Test #{}".format(testid))
            #
            execute_stdin = open(os.path.join(problem, test['input']), "r")
            execute_stdout = open("stdout", "w")
            execute_res = executor_s.execute(full_args.execute, timelimit=time_limit, stdin=execute_stdin, stdout=execute_stdout, limit_syscall=True, timeratio=lang['execute'].get('timeratio', 1.0))
            execute_stdout.close()
            execute_stdin.close()
            #
            this_detail['input'] = func.read_first_bytes(os.path.join(problem, test['input']))
            this_detail['exe_time'] = execute_res.exe_time
            this_detail['exe_memory'] = execute_res.exe_memory
            if execute_res.exe_time > exe_time:
                exe_time = execute_res[2]
            if execute_res.exe_memory > exe_memory:
                exe_memory = execute_res[1]
            if execute_res.exit_reason != 'none':
                verdict = execute_res.exit_reason
                detail.append(this_detail)
                break
            this_detail['answer'] = func.read_first_bytes(os.path.join(problem, test['output']))
            this_detail['your output'] = func.read_first_bytes("stdout")
            # TODO: checker按checker的语言来跑
            checker_cmd = [os.path.join(problem, problem_yaml['checker'].get('exe', problem_yaml['checker']['source'] + '.exe')), os.path.join(problem, test['input']), os.path.join(problem, test['output']), 'stdout']
            log.append("running checker ({}) to check the answer\n".format(problem_yaml['checker'].get('exe', problem_yaml['checker']['source'] + '.exe')))
            checker_stdout = open('chk_stdout', 'w')
            checker_res = executor.execute(checker_cmd, timelimit=time_limit, stdout=checker_stdout, stderr=checker_stdout)
            checker_stdout.close()
            this_detail['checker'] = func.read_first_bytes("chk_stdout")
            if checker_res[3] != 0:
                verdict = 'WA'
                detail.append(this_detail)
                break
    except Exception as e:
        traceback.print_exc()
        logging.error(e)
    finally:
        # 切个毛线切，搞完收工走人
        session_time = time.time() - session_start
        return JudgeResult(verdict, exe_time, int(exe_memory / 1024), 0, session_time, detail)

