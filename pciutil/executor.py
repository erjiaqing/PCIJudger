'''
executor.py

To warp different executors
such as lrun, lorun, ptrace-like or other sandboxes
and provide a unique api to run and get results
'''

import subprocess
import logging, time, os

from . import log as logger

# to execute some command
# with out a shell
# timelimit: Limit the time
# stdin: redirect stdin
# stdout: redirect stdout
# stderr: redirect stderr
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
        timelimit *= timeratio
        exe = subprocess.Popen(cmd, stdin=stdin, stdout=stdout, stderr=stderr, env=os.environ.copy())
        exeStart = time.time()
        while exe.poll() == None:
            if time.time() - exeStart > 1 + timelimit:
                exe.kill()
                log.append('exitcode={} time={:0.3}'.format(exe.returncode, (time.time() - exeStart)/timeratio))
                return (True, 1, time.time() - exeStart, 0, log, 'TLE')
            time.sleep(0.01)
        exeTime = time.time() - exeStart
        return (True, 0, exeTime/timeratio, exe.returncode, None, 'none')
    except OSError:
        return (False, 0, 0., -1, None, 'SE')
    except ValueError:
        return (False, 0, 0., -1, None, 'SE')
    except Exception as e:
        logging.error('Unknown error: {}'.format(e))
        return (False, 0, 0., -1, None, 'SE')
