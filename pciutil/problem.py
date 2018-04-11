import json, yaml, os, sys, shutil, time
import logging, traceback, time, base64
import tarfile, re
import subprocess, traceback

from . import executor, compiler, func
from . import log as logger

class CompileResult:
    def __init__(self, success, log, output=None):
        self.success = success
        self.output = output
        self.log = log

def compile_problem(conf, problem, dest):
    # 先创建一份试题的副本
    logging.debug("Compile problem %s -> %s", problem, dest)
    func.copytree(problem, dest)
    current_dir = os.getcwd()
    # 切到试题所在的目录，然后编译
    os.chdir(dest)
    logging.debug("Current at %s", dest)
    with open("problem.yaml", "r") as problemyaml_fp:
        problem_meta = yaml.load(problemyaml_fp)
    compile_log = ""
    success = True
    while True:
        compile_log += "Compiling checker"
        checker = problem_meta.get("checker", False)
        if not checker:
            compile_log += "source code of checker not found\n"
            success = False
            break
        with open(os.path.join(conf['lang'], checker['lang'] + '.yaml')) as lang_conf_fp:
            lang_conf = yaml.load(lang_conf_fp)
        result = compiler.compile(lang_conf, os.getcwd(), checker['source'], checker.get('exe', checker['source'] + '.exe'))
        if not result.success:
            compile_log += "compile checker with failure\n"
            compile_log += result.compiler_output
            success = False
            break
        break
    while True:
        compile_log += "Compiling interactor"
        checker = problem_meta.get("interactor", False)
        if not checker:
            compile_log += "source code of interactor not found\n"
            break
        with open(os.path.join(conf['lang'], checker['lang'] + '.yaml')) as lang_conf_fp:
            lang_conf = yaml.load(lang_conf_fp)
        result = compiler.compile(lang_conf, os.getcwd(), checker['source'], checker.get('exe', checker['source'] + '.exe'))
        if not result.success:
            compile_log += "compile interactor with failure\n"
            compile_log += result.compiler_output
            success = False
            break
        break
    # 退回到开始的目录
    os.chdir(current_dir)
    return CompileResult(success, compile_log)

def get_problem(conf, problem, problem_git, version):
    logging.info("Get problem: %s", problem_git)
    curdir = os.getcwd()
    try:
        problem_dir = os.path.join(conf['datapath'], problem)
        tmpdir_name = base64.b32encode(os.urandom(10)).decode('utf-8')
        tmpdir_full = os.path.join(conf['tmp'], tmpdir_name)
        os.chdir(conf['tmp'])
        # 然后clone
        subprocess.run([conf['git'], 'clone', problem_git, tmpdir_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        os.chdir(tmpdir_full)
        if version != '':
            subprocess.run([conf['git'], 'checkout', version], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # 编译
        try:
            shutil.rmtree(problem_dir)
        except:
            pass
        compile_problem(conf, tmpdir_full, problem_dir)
        os.chdir(curdir)
        shutil.rmtree(tmpdir_full)
    except:
        logging.traceback.print_stack()
        os.chdir(curdir)
        return False
    return True

def check_problem(conf, problem, expected_version):
    res = False
    curdir = os.getcwd()
    try:
        problem_dir = os.path.join(conf['datapath'], problem)
        os.chdir(problem_dir)
        version_output = subprocess.run([conf['git'], 'rev-parse', 'HEAD'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        current_version_hash = version_output.stdout.decode('utf-8', 'ignore')
        if current_version_hash != expected_version and expected_version != '':
            res = False
        else:
            res = True
    except:
        res = False
    finally:
        os.chdir(curdir)
        return res
