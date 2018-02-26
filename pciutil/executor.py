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
    log = logger.PCILog("executor")
    log.append(" ".join(cmd))
    logging.debug('will execute: {cmd}'.format(cmd=cmd))
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
        log.append('exitcode={} time={:0.3}'.format(exe.returncode, exeTime))
        return (True, 0, exeTime/timeratio, exe.returncode, log, 'none')
    except OSError:
        logging.error('Cannot execute')
        log.append('cannot execute')
        return (False, 0, 0., -1, log, 'SE')
    except ValueError:
        logging.error('Wrong arguments')
        log.append('wrong arguments')
        return (False, 0, 0., -1, log, 'SE')
    except Exception as e:
        logging.error('Unknown error: {}'.format(e))
        log.append('unknown error')
        return (False, 0, 0., -1, log, 'SE')
