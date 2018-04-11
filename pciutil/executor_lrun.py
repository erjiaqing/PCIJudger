'''
executor.py

To warp different executors
such as lrun, lorun, ptrace-like or other sandboxes
and provide a unique api to run and get results
'''

import subprocess
import logging, time, os, yaml, tempfile

# to execute some command
# with out a shell
# timelimit: Limit the time
# stdin: redirect stdin
# stdout: redirect stdout
# stderr: redirect stderr

class ExecuteResult:
    def __init__(self, exe_time, exe_memory, exit_code, exit_signal, exit_reason):
        self.exe_time = exe_time
        self.exe_memory = exe_memory
        self.exit_code = exit_code
        self.exit_signal = exit_signal
        self.exit_reason = exit_reason

def execute_interactor(program, interactor, timelimit=None, memorylimit=None, timeratio=1., chroot="", forbidden_path=[], limit_syscall=False, stdoutFile=None, stderr=None):
    if timelimit == None:
        timelimit = 1
    if memorylimit == None:
        memorylimit = 512 * 1024 * 1024
    if stderr == None:
        stderr = subprocess.DEVNULL
    try:
        ##
        pr, iw = os.pipe()
        pr = os.fdopen(pr, 'r')
        iw = os.fdopen(iw, 'w')
        ir, pw = os.pipe()
        ir = os.fdopen(ir, 'r')
        pw = os.fdopen(pw, 'w')
        ##
        stdout = open("output", 'w')
        ##
        cpu_tl = timelimit * timeratio
        real_tl = cpu_tl * 1.5
        result_yaml = open('result.yaml', 'w')
        rcmd = ['/usr/local/bin/lrun', '--max-real-time', str(real_tl), '--max-cpu-time', str(cpu_tl), '--max-stack', '536870912', '--max-memory', str(memorylimit), '--network', 'false', '--result-fd', str(result_yaml.fileno())]
        if limit_syscall:
            rcmd.extend(['--chroot', chroot])
            rcmd.extend(['--remount-dev', 'true'])
            rcmd.extend(['--chdir', '/fj_tmp'])
            rcmd.extend(['--syscalls', '!execve,flock,ptrace,sync,fdatasync,fsync,msync,sync_file_range,syncfs,unshare,setns,clone[a&268435456==268435456],query_module,sysinfo,syslog,sysfs'])
        rcmd.append('--')
        rcmd.extend(program)
        ######
        interact_yaml = open('interact.yaml', 'w')
        icmd = ['/usr/local/bin/lrun', '--max-real-time', str(real_tl), '--max-cpu-time', str(cpu_tl), '--max-stack', '536870912', '--max-memory', str(memorylimit), '--network', 'false', '--result-fd', str(interact_yaml.fileno())]
        icmd.append('--')
        icmd.extend(interactor)
        ######
        logging.info(' '.join(icmd))
        exeI = subprocess.Popen(icmd, stdin=ir, stdout=iw, stderr=stderr, env=os.environ.copy(), pass_fds=(interact_yaml.fileno(), ))
        exe = subprocess.Popen(rcmd, stdin=pr, stdout=pw, stderr=subprocess.DEVNULL, env=os.environ.copy(), pass_fds=(result_yaml.fileno(),))
        exe.wait()
        exeI.wait()
        pr.close()
        pw.close()
        iw.close()
        ir.close()
        result_yaml.close()
        interact_yaml.close()
        with open("result.yaml", 'r') as result_fp:
            result = yaml.load(result_fp)
        exit_reason = 'none'
        if result['exceeded'] == 'REAL_TIME':
            exeTime = result['realtime'] / timeratio
        else:
            exeTime = result['cputime'] / timeratio
        exeMemory = result['memory']
        exitcode = 0
        if result['exceeded'] == 'REAL_TIME' or result['exceeded'] == 'CPU_TIME':
            exit_reason = 'TLE'
        elif result['exceeded'] == 'MEMORY':
            exit_reason = 'MLE'
        elif result['exitsig'] != 0:
            exitcode = -result['exitsig']
            exit_reason = 'RE'
        elif result['exitcode'] != 0:
            exitcode = result['exitcode']
            exit_reason = 'RE'
        elif result['termsig'] != 0:
            exitcode = -result['termsig']
            exit_reason = 'RE'
        with open("interact.yaml", 'r') as result_fp:
            result = yaml.load(result_fp)
        exit_reason = 'none'
        if result['exceeded'] == 'REAL_TIME':
            exeTime = result['realtime'] / timeratio
        else:
            exeTime = result['cputime'] / timeratio
        exeMemory = result['memory']
        exitcode = 0
        if result['exceeded'] == 'REAL_TIME' or result['exceeded'] == 'CPU_TIME':
            exit_reason = 'WA'
        elif result['exceeded'] == 'MEMORY':
            exit_reason = 'WA'
        elif result['exitsig'] != 0:
            exitcode = -result['exitsig']
            exit_reason = 'WA'
        elif result['exitcode'] != 0:
            exitcode = result['exitcode']
            exit_reason = 'WA'
        elif result['termsig'] != 0:
            exitcode = -result['termsig']
            exit_reason = 'WA'
        return ExecuteResult(exeTime, exeMemory, exitcode, result['termsig'], exit_reason)
    except OSError as e:
        logging.exception('OSError: {}'.format(e))
        return ExecuteResult(-1, -1, -1, -1, 'SE')
    except ValueError:
        logging.error('Wrong arguments')
        return ExecuteResult(-1, -1, -1, -1, 'SE')
    except Exception as e:
        logging.exception('Unknown error: {}'.format(e))
        return ExecuteResult(-1, -1, -1, -1, 'SE')

def execute(cmd, timelimit=None, memorylimit=None, timeratio=1., chroot="", forbidden_path=[], limit_syscall=False, stdin=None, stdout=None, stderr=None):
    if timelimit == None:
        timelimit = 1
    if memorylimit == None:
        memorylimit = 512 * 1024 * 1024
    if stdin == None:
        stdin = subprocess.DEVNULL
    if stdout == None:
        stdout = subprocess.DEVNULL
    if stderr == None:
        stderr = subprocess.DEVNULL
    try:
        cpu_tl = timelimit * timeratio
        real_tl = cpu_tl * 1.5
        result_yaml = open('result.yaml', 'w')
        rcmd = ['/usr/local/bin/lrun', '--max-real-time', str(real_tl), '--max-cpu-time', str(cpu_tl), '--max-stack', '536870912', '--max-memory', str(memorylimit), '--network', 'false', '--result-fd', str(result_yaml.fileno())]
        if limit_syscall:
            rcmd.extend(['--chroot', chroot])
            rcmd.extend(['--remount-dev', 'true'])
            rcmd.extend(['--chdir', '/fj_tmp'])
            rcmd.extend(['--syscalls', '!execve,flock,ptrace,sync,fdatasync,fsync,msync,sync_file_range,syncfs,unshare,setns,clone[a&268435456==268435456],query_module,sysinfo,syslog,sysfs'])
        rcmd.append('--')
        rcmd.extend(cmd)
        exe = subprocess.Popen(rcmd, stdin=stdin, stdout=stdout, stderr=stderr, env=os.environ.copy(), pass_fds=(result_yaml.fileno(),))
        exe.wait()
        result_yaml.close()
        with open("result.yaml", 'r') as result_fp:
            result = yaml.load(result_fp)
        exit_reason = 'none'
        if result['exceeded'] == 'REAL_TIME':
            exeTime = result['realtime'] / timeratio
        else:
            exeTime = result['cputime'] / timeratio
        exeMemory = result['memory']
        exitcode = 0
        if result['exceeded'] == 'REAL_TIME' or result['exceeded'] == 'CPU_TIME':
            exit_reason = 'TLE'
        elif result['exceeded'] == 'MEMORY':
            exit_reason = 'MLE'
        elif result['exitsig'] != 0:
            exitcode = -result['exitsig']
            exit_reason = 'RE'
        elif result['exitcode'] != 0:
            exitcode = result['exitcode']
            exit_reason = 'RE'
        elif result['termsig'] != 0:
            exitcode = -result['termsig']
            exit_reason = 'RE'
        return ExecuteResult(exeTime, exeMemory, exitcode, result['termsig'], exit_reason)
    except OSError:
        return ExecuteResult(-1, -1, -1, -1, 'SE')
    except ValueError:
        logging.error('Wrong arguments')
        return ExecuteResult(-1, -1, -1, -1, 'SE')
    except Exception as e:
        logging.exception('Unknown error: {}'.format(e))
        return ExecuteResult(-1, -1, -1, -1, 'SE')
