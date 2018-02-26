#!/usr/bin/python3
import json, yaml, os, sys, shutil
import logging, traceback, time, base64
import tarfile, re
import argparse

from pciutil import func, judger

LOGGING_FORMAT = '%(asctime)s %(levelname)8s : %(message)s'
logging.basicConfig(format=LOGGING_FORMAT, datefmt='%Y-%m-%d %H:%M:%S', level=logging.DEBUG)

conf = {}

def check_or_create(path):
    if not os.path.exists(path):
        os.makedirs(path)

if __name__ == '__main__':
    # load conf
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--problem', default="/problem")
    parser.add_argument('--code', default="/code/code")
    parser.add_argument('--language', default="")
    if sys.argv[0] == 'python' or sys.argv[0] == 'python3':
        arguments = parser.parse_args(sys.argv[2:])
    else:
        arguments = parser.parse_args(sys.argv[1:])
    try:
        with open('judger.yaml', 'r') as conf_fp:
            conf = yaml.load(conf_fp)
    except:
        logging.error('Cannot load "%s"', 'judger.yaml')
        sys.exit(-1)
    conf['cwd'] = os.getcwd()
    if conf.get('datapath', False) == False:
        conf['datapath'] = os.path.join(conf['cwd'], 'data')
        check_or_create(conf['datapath'])
    if conf.get('tmp', False) == False:
        conf['tmp'] = os.path.join(conf['cwd'], 'tmp')
    check_or_create(conf['tmp'])
    conf['lang'] = os.path.join(conf['cwd'], 'lang')
    check_or_create(conf['lang'])
    #
    if not os.path.isfile(os.path.join(conf['lang'], arguments.language + '.yaml')):
        os.exit(1)
    #
    judge_res = judger.judge(conf, os.path.join(conf['lang'], arguments.language + '.yaml'), arguments.code, arguments.problem)
    print(json.dumps(vars(judge_res), indent=4, sort_keys=True))
