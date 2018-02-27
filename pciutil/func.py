import os, logging

def format_list(lst, fmt):
    ret = []
    for item in lst:
        ret.append(item.format(**fmt))
    return ret

def check_or_create(path):
    if not os.path.exists(path):
        logging.info('Path %s does not exist', path)
        os.makedirs(path)
        
def read_first_bytes(path):
    if True:
        with open(path, 'rb') as inputfile:
            if os.path.getsize(path) > 64 + 32:
                ret = inputfile.read(64).decode('utf-8', 'backslashreplace') + '...({} bytes)'.format(os.path.getsize(path) - 64)
            else:
                ret = inputfile.read().decode('utf-8', 'backslashreplace')
        return ret
    #except:
    #    return '(unable to read file)'
