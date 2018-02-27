#!/usr/bin/python3
import argparse, random, string, sys, os
from subprocess import call

def check_or_create(path):
    if not os.path.exists(path):
        os.makedirs(path)

if __name__ == '__main__':
    # load conf
    rand_str = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(10))
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--problem', default="/problem")
    parser.add_argument('--code', default="/code/code")
    parser.add_argument('--language', default="")
    parser.add_argument('--tmp', default="/tmp/_fj_{}".format(rand_str))
    if sys.argv[0] == 'python' or sys.argv[0] == 'python3':
        arguments = parser.parse_args(sys.argv[2:])
    else:
        arguments = parser.parse_args(sys.argv[1:])
    check_or_create(arguments.tmp)
    call(["docker", "run", "--privileged", "--mount", "type=bind,source={},target=/problem,readonly".format(arguments.problem), "--mount", "type=bind,source={},target=/code/code,readonly".format(arguments.code), "--mount", "type=bind,source={},target=/fj_tmp".format(arguments.tmp), "erjiaqing/finaljudge", "--language", arguments.language, "--problemrealpath", os.path.join(arguments.problem)])
