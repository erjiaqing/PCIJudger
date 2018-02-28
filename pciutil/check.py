import json, yaml, os, sys, shutil, time
import logging, traceback, time, base64
import tarfile, re
import subprocess, traceback
import string

from . import executor, compiler, judger, func, log, problem

class CheckerResult:
    def __init__(self, success, log):
        self.success = success
        self.log = log

class Checker:
    def __init__(self, conf, root):
        self.conf = conf
        self.root = root

    def process_work(self):
        old_cwd = os.getcwd()
        vresult = True
        result_json = []
        try:
            # problem path: /problem
            # 先拷贝一份题目到临时文件夹，因为不能修改指定的文件夹
            # 在用docker调用的时候，check是指检查一个给定的目录下面的试题
            tmpdir = base64.b32encode(os.urandom(10)).decode('utf-8')
            basedir = os.path.join(self.conf['tmp'], tmpdir)
            problem_source_dir = '/problem'
            func.copytree(problem_source_dir, basedir)
            os.chdir(basedir)
            # 编译题目
            compile_problem_log = log.PCILog("build")
            compile_problem_log.append("build problem")
            compiled_problem_dir = os.path.join(self.conf['tmp'], base64.b32encode(os.urandom(10)).decode('utf-8'))
            start_time = time.time()
            logging.info('build problem')
            problem_compile_result = problem.compile_problem(self.conf, os.getcwd(), compiled_problem_dir)
            logging.info('problem built')
            problem_compile_time = time.time() - start_time
            compile_problem_log.append(problem_compile_result.log)
            result_json.append(dict(name="build problem", time=problem_compile_time, output=compile_problem_log.to_array()))
            if not problem_compile_result.success:
                shutil.rmtree(compiled_problem_dir)
                raise Exception("Failed to build problem")
            # 读取pci.yaml中的配置
            with open("pci.yaml", 'r') as pcitask_fp:
                pcitask = yaml.load(pcitask_fp)
            # 执行pci.yaml中的任务
            for subtask in pcitask['step']:
                tresult = dict(name=subtask['name'])
                stepoutput = log.PCILog("subtask.{}".format(subtask['name']))
                tot_exe_time = time.time()
                success = True
                for cmd in subtask['cmd']:
                    lang = cmd['file']['lang']
                    src = cmd['file']['source']
                    lang_file = os.path.join(self.conf['lang'], lang + '.yaml')
                    stepoutput.append("command={} file={} language={}\n".format(cmd['type'], src, lang))
                    with open(lang_file, 'r') as lang_fp:
                        lang_file_c = yaml.load(lang_fp)
                    if cmd['type'] == 'compile':
                        logging.info('Compile %s', src)
                        result = compiler.compile(lang_file_c, os.getcwd(), src)
                        stepoutput.append("Compiler Output:\n{}".format(result.compiler_output))
                        if not result.success:
                            success = False
                            break
                    elif cmd['type'] == 'judge':
                        logging.info('Judge %s, expect (%s)', src, ', '.join(cmd['expect']))
                        result = judger.judge(self.conf, lang_file, os.path.join(os.getcwd(), cmd['file']['source']), compiled_problem_dir)
                        stepoutput.append("judger returned with {}, exe_time: {}, exit code: {}".format(result.verdict, result.used_time, result.exit_code))
                        expected_result = False
                        for v in cmd['expect']:
                            if v == result.verdict:
                                expected_result = True
                                break
                        if not expected_result:
                            stepoutput.append("Unexpected result!")
                            success = False
                            break
                tresult['output'] = stepoutput.to_array()[:]
                tresult['time'] = time.time() - tot_exe_time
                result_json.append(tresult)
                stepoutput = None
                if not success:
                    vresult = False
                    break
            pass
        except Exception as e:
            logging.error(e)
            traceback.print_exc()
            result = False
        finally:
            os.chdir(old_cwd)
            shutil.rmtree(basedir)
            try:
                shutil.rmtree(compiled_problem_dir)
            except:
                pass
            return CheckerResult(vresult, result_json)
