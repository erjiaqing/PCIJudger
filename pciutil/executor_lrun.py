'''
executor.py

To warp different executors
such as lrun, lorun, ptrace-like or other sandboxes
and provide a unique api to run and get results
'''

import subprocess
import logging, time, os, yaml

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

def execute(cmd, timelimit=None, memorylimit=None, timeratio=1., limit_syscall=False, stdin=None, stdout=None, stderr=None):
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
        elif result['exceeded'] == 'MEMORY'
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
        logging.error('Unknown error: {}'.format(e))
        return ExecuteResult(-1, -1, -1, -1, 'SE')
