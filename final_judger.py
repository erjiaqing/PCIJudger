#!/usr/bin/python3
import argparse, random, string, json, sys, os
import subprocess

def check_or_create(path):
    if not os.path.exists(path):
        os.makedirs(path)

def judge(problem, code, language, tmpdir):
    res = subprocess.run(["docker", "run", "--privileged", "--mount", "type=bind,source={},target=/problem,readonly".format(problem), "--mount", "type=bind,source={},target=/code/code,readonly".format(code), "--mount", "type=bind,source={},target=/fj_tmp".format(tmpdir), "erjiaqing/finaljudge", "--language", language, '--action', 'judge'], stdout=subprocess.PIPE)
    return json.loads(res.stdout.decode('utf-8'))

def build(problem, dest, tmpdir):
    res = subprocess.run(["docker", "run", "--privileged", "--mount", "type=bind,source={},target=/problem,readonly".format(problem), "--mount", "type=bind,source={},target=/code".format(dest), "--mount", "type=bind,source={},target=/fj_tmp".format(tmpdir), "erjiaqing/finaljudge", '--action', 'build'], stdout=subprocess.PIPE)
    return True

def check(problem, tmpdir):
    res = subprocess.run(["docker", "run", "--privileged", "--mount", "type=bind,source={},target=/problem,readonly".format(problem), "--mount", "type=tmpfs,target=/code", "--mount", "type=bind,source={},target=/fj_tmp".format(tmpdir), "erjiaqing/finaljudge", '--action', 'check'], stdout=subprocess.PIPE)
    return json.loads(res.stdout.decode('utf-8'))

if __name__ == '__main__':
    # load conf
    rand_str = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(10))
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--problem', default="/problem")
    parser.add_argument('--code', default="/code/code")
    parser.add_argument('--language', default="")
    parser.add_argument('--tmp', default="/tmp/_fj_{}".format(rand_str))
    parser.add_argument('--action', default='judge')
    parser.add_argument('--dest', default='/code')
    if sys.argv[0] == 'python' or sys.argv[0] == 'python3':
        arguments = parser.parse_args(sys.argv[2:])
    else:
        arguments = parser.parse_args(sys.argv[1:])
    check_or_create(arguments.tmp)
    if arguments.action == 'judge':
        print(json.dumps(judge(arguments.problem, arguments.code, arguments.language, arguments.tmp), indent=2))
    elif arguments.action == 'build':
        print(json.dumps(build(arguments.problem, arguments.dest, arguments.tmp), indent=2))
    elif arguments.action == 'check':
        print(json.dumps(check(arguments.problem, arguments.tmp), indent=2))
    else:
        sys.exit(1)
