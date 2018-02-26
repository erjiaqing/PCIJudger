import json, yaml, os, sys, shutil, time
import logging, traceback, time, base64
import tarfile, re
import subprocess, traceback
import string

from . import executor, compiler, judger, func, log

class CheckerResult:
    def __init__(self, success, log):
        self.success = success
        self.log = log

class Checker:
    def __init__(self, conf, root):
        self.conf = conf
        self.root = root
    
    def git_fetch(self, repo, version, stdout_fp, stderr_fp):
        git_log = log.PCILog("git.fetch")
        tmpdir = base64.b32encode(os.urandom(10)).decode('utf-8')
        subprocess.run(["git", "clone", repo, tmpdir], stdin=None, stdout=stdout_fp, stderr=stderr_fp, check=True)
        git_log.append(" ".join(["git", "clone", repo, tmpdir]))
        os.chdir(os.path.join(os.getcwd(), tmpdir))
        subprocess.run(["git", "checkout", version], stdin=None, stdout=stdout_fp, stderr=stderr_fp, check=True)
        git_log.append(" ".join(["git", "checkout", version]))
        return git_log

    def process_work(self, task):
        old_cwd = os.getcwd()
        result = True
        result_json = []
        try:
            tmpdir = base64.b32encode(os.urandom(10)).decode('utf-8')
            basedir = os.path.join(self.conf['tmp'], tmpdir)
            func.check_or_create(basedir)
            os.chdir(basedir)
            git_log = log.PCILog("git")
            git_log.append("git clone")
            start_time = time.time()
            git_log.merge(self.git_fetch(task['problem']['clone_url'], task['param']['sha'], None, None))
            git_time = time.time() - start_time
            result_json.append(dict(name="git", time=git_time, output=git_log.to_array()))
            # 编译题目
            compile_problem_log = log.PCILog("build")
            compile_problem_log.append("build problem")
            compiled_problem_dir = os.path.join(self.conf['tmp'], base64.b32encode(os.urandom(10)).decode('utf-8'))
            start_time = time.time()
            problem_compile_result = judger.compile_problem(self.conf, os.getcwd(), compiled_problem_dir)
            problem_compile_time = time.time() - start_time
            compile_problem_log.append(problem_compile_result.log)
            result_json.append(dict(name="build problem", time=problem_compile_time, output=compile_problem_log.to_array()))
            print(result_json)
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
                        lang_file = yaml.load(lang_fp)
                    if cmd['type'] == 'compile':
                        result = compiler.compile(lang_file, os.getcwd(), src)
                        stepoutput.append("Compiler Output:\n{}".format(result.compiler_output))
                        if not result.success:
                            success = False
                            break
                    elif cmd['type'] == 'judge':
                        result = judger.judge(self.conf, lang_file, os.path.join(os.getcwd(), cmd['file']['source']), compiled_problem_dir)
                        stepoutput.merge(result.log)
                        stepoutput.append("judger returned with {}, exe_time: {}, exit code: {}".format(result.result, result.used_time, result.exit_code))
                        expected_result = False
                        for v in cmd['expect']:
                            if v == result.result:
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
                    result = False
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
            return CheckerResult(result, result_json)
