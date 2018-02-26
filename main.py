import requests, json, yaml, os, sys, shutil
import logging, traceback, time, base64
import tarfile, re

from pciutil import check, func, executor, judger

LOGGING_FORMAT = '%(asctime)s %(levelname)8s : %(message)s'
logging.basicConfig(format=LOGGING_FORMAT, datefmt='%Y-%m-%d %H:%M:%S', level=logging.DEBUG)

conf = {}

def request_task():
    global conf
    try:
        r = requests.get(conf['_getnew'])
        return (True, r.json())
    except:
        return (False, None)

def push_result(key, result, log):
    global conf
    real_result = "failure"
    if result:
        real_result = "success"
    r = requests.post(conf['_pushresult'], dict(key=key, log=json.dumps(log), result=real_result))

def normal_run():
    global conf
    task = request_task()
    if task[0] and task[1]['data']:
        new_task = task[1]['data']
        if new_task['type'] == 'check':
            checker = check.Checker(conf, os.getcwd())
            result = checker.process_work(new_task)
        elif new_task['type'] == 'judge':
            judger_obj = judger.Judger(conf, new_task['problem']['repo'], new_task['param']['submission'], new_task)
            result = judger_obj.judge()
        push_result(new_task['update_key'], result.success, result.log)

def check_or_create(path):
    if not os.path.exists(path):
        logging.info('Path %s does not exist', path)
        os.makedirs(path)

if __name__ == '__main__':
    # load conf
    logging.info('Starting WOJ Polygon Judger')
    logging.debug('Loading "judger.yaml"')
    try:
        with open('judger.yaml', 'r') as conf_fp:
            conf = yaml.load(conf_fp)
    except:
        logging.error('Cannot load "%s"', 'judger.yaml')
        sys.exit(-1)
    conf['cwd'] = os.getcwd()
    conf['datapath'] = os.path.join(conf['cwd'], 'data')
    conf['tmp'] = os.path.join(conf['cwd'], 'tmp')
    conf['lang'] = os.path.join(conf['cwd'], 'lang')
    conf['checker'] = os.path.join(conf['cwd'], 'checker')
    conf['compile_cache'] = os.path.join(conf['cwd'], 'compile_cache')
    logging.debug('Current working dir is %s', conf['cwd'])
    logging.debug('Will find judge data in %s', conf['datapath'])
    logging.debug('Tempory dir is %s', conf['tmp'])
    logging.debug('Language configure path is %s', conf['lang'])
    logging.debug('Checker dir is %s', conf['checker'])
    logging.debug('compile cache: %s', conf['compile_cache'])
    check_or_create(conf['datapath'])
    check_or_create(conf['tmp'])
    check_or_create(conf['lang'])
    check_or_create(conf['checker'])
    check_or_create(conf['compile_cache'])
    # generate routes
    conf['_getnew'] = conf['server'] + '/api/worker/request?auth=whuacm2018'
    conf['_pushresult'] = conf['server'] + '/api/worker/push?auth=whuacm2018'
    logging.debug('get new tasks: %s', conf['_getnew'])
    logging.debug('push results: %s', conf['_pushresult'])
    # end of generate routes
    logging.debug('Judger started')
    logging.info('Waiting for new task')
    while True:
        normal_run()
        time.sleep(5)
