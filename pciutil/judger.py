import json, yaml, os, sys, shutil, time
import logging, traceback, time, base64, hashlib
import tarfile, re
import subprocess, traceback

from . import compiler, func, problem
from . import executor_lrun as executor_s
from . import executor as executor

class JudgeResult:
    def __init__(self, result, exe_time, exe_memory, exit_code, used_time, detail):
        self.success = True
        self.verdict = result
        self.exe_time = exe_time
        self.exe_memory = exe_memory
        self.exit_code = exit_code
        self.used_time = used_time
        self.detail = detail

def judge(conf, lang_file, code, problem):
    current_dir = os.getcwd()
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
        os.chdir(working_dir)
        # 计算编译和运行的参数
        full_args = compiler.get_execute_command(lang, code, os.getcwd(), True)
        # load problem.yaml
        with open(os.path.join(problem, "problem.yaml"), "r") as problem_yaml_fp:
            problem_yaml = yaml.load(problem_yaml_fp)
        # leetcode模式
        code_template = problem_yaml.get('template', False)
        template_header = b''
        template_footer = b''
        lang_base = os.path.basename(lang_file)
        if code_template != False:
            try:
                with open(os.path.join(problem, code_template + ".header." + lang_base[:-5]), 'rb') as header:
                    template_header = header.read()
            except Exception as e:
                logging.exception(e)
            try:
                with open(os.path.join(problem, code_template + ".footer." + lang_base[:-5]), 'rb') as footer:
                    template_footer = footer.read()
            except Exception as e:
                logging.exception(e)
        # 写文件
        src_file = open(full_args.source, 'wb')
        with open(code, 'rb') as src:
            src_file.write(template_header)
            src_file.write(src.read())
            src_file.write(template_footer)
        src_file.close()
        # If this problem requires extern files to compile or run, copy them to tmp
        extern_files = problem_yaml.get('additionalLibrary', [])
        for ext_file in extern_files:
            shutil.copy(os.path.join(problem, ext_file), ext_file)
        # 编译
        result = compiler.compile(lang, os.getcwd(), full_args.source)
        if result.compiler_output != "":
            detail.append(dict(name="Compiler", output=result.compiler_output))
        if result.exit_code != 0:
            verdict = "CE"
            raise Exception("CE")
        # 评测
        time_limit = int(problem_yaml.get('time', 1000)) / 1000
        verdict = "AC"
        testid = 0
        chroot_name = base64.b32encode(os.urandom(10)).decode('utf-8')
        executor.execute(['/usr/local/bin/lrun-mirrorfs', '--name', chroot_name, '--setup', '/fj/mirrorfs.conf'])
        for test in problem_yaml['case']:
            testid += 1
            logging.info('Judge on test #{}'.format(testid))
            this_detail = dict(name="Test #{}".format(testid))
            #
            inter = problem_yaml.get('interactor', False)
            if inter:
                logging.info("User interactor")
                inter_err = open('inter_err', 'w')
                inter_cmd = [os.path.join(problem, problem_yaml['interactor'].get('exe', problem_yaml['interactor']['source'] + '.exe'))]
                inter_cmd.append(os.path.join(problem, test['input']))
                inter_cmd.append(os.path.join(os.getcwd(), "stdout"))
                inter_cmd.append(os.path.join(problem, test['output']))
                execute_res = executor_s.execute_interactor(full_args.execute, inter_cmd, chroot=os.path.join('/fj_tmp/mirrorfs/', chroot_name), forbidden_path=[], timelimit=time_limit, limit_syscall=True, timeratio=lang['execute'].get('timeratio', 1.0), stderr=inter_err)
                inter_err.close()
                this_detail['interactor output'] = func.read_first_bytes("inter_err")
            else:
                execute_stdin = open(os.path.join(problem, test['input']), "r")
                execute_stdout = open("stdout", "w")
                execute_res = executor_s.execute(full_args.execute, chroot=os.path.join('/fj_tmp/mirrorfs/', chroot_name), forbidden_path=[], timelimit=time_limit, stdin=execute_stdin, stdout=execute_stdout, limit_syscall=True, timeratio=lang['execute'].get('timeratio', 1.0))
                execute_stdout.close()
                execute_stdin.close()
            #
            this_detail['input'] = func.read_first_bytes(os.path.join(problem, test['input']))
            this_detail['exe_time'] = execute_res.exe_time
            this_detail['exe_memory'] = execute_res.exe_memory
            if execute_res.exe_time > exe_time:
                exe_time = execute_res.exe_time
            if execute_res.exe_memory > exe_memory:
                exe_memory = execute_res.exe_memory
            if execute_res.exit_reason != 'none':
                verdict = execute_res.exit_reason
                this_detail['verdict'] = verdict
                detail.append(this_detail)
                logging.info("Test #{}: {} exetime={} exememory={}".format(testid, this_detail['verdict'], this_detail['exe_time'], this_detail['exe_memory']))
                break
            this_detail['answer'] = func.read_first_bytes(os.path.join(problem, test['output']))
            this_detail['your output'] = func.read_first_bytes("stdout")
            # TODO: checker按checker的语言来跑
            checker_cmd = [os.path.join(problem, problem_yaml['checker'].get('exe', problem_yaml['checker']['source'] + '.exe')), os.path.join(problem, test['input']), 'stdout', os.path.join(problem, test['output'])]
            checker_stdout = open('chk_stdout', 'w')
            checker_res = executor.execute(checker_cmd, timelimit=time_limit, stdout=checker_stdout, stderr=checker_stdout)
            checker_stdout.close()
            this_detail['checker'] = func.read_first_bytes("chk_stdout")
            if checker_res[3] != 0:
                verdict = 'WA'
                this_detail['verdict'] = verdict
                detail.append(this_detail)
                logging.info("Test #{}: {} exetime={} exememory={}".format(testid, this_detail['verdict'], this_detail['exe_time'], this_detail['exe_memory']))
                break
            this_detail['verdict'] = verdict
            logging.info("Test #{}: {} exetime={} exememory={}".format(testid, this_detail['verdict'], this_detail['exe_time'], this_detail['exe_memory']))
            detail.append(this_detail)
    except Exception as e:
        if e != "CE":
            logging.exception(e)
    finally:
        # 切个毛线切，搞完收工走人
        session_time = time.time() - session_start
        try:
            executor.execute(['/usr/local/bin/lrun-mirrorfs', '--name', chroot_name, '--teardown', '/fj/mirrorfs.conf'])
        except:
            pass
        os.chdir(current_dir)
        return JudgeResult(verdict, exe_time, int(exe_memory / 1024), 0, session_time, detail)

