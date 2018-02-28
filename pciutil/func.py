import os, logging, shutil

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
    
def copytree(src, dst, symlinks=False):
    names = os.listdir(src)
    try:
        os.makedirs(dst)
    except:
        pass
    errors = []
    for name in names:
        srcname = os.path.join(src, name)
        dstname = os.path.join(dst, name)
        try:
            if symlinks and os.path.islink(srcname):
                linkto = os.readlink(srcname)
                os.symlink(linkto, dstname)
            elif os.path.isdir(srcname):
                copytree(srcname, dstname, symlinks)
            else:
                shutil.copy2(srcname, dstname)
            # XXX What about devices, sockets etc.?
        except (IOError, os.error) as why:
            errors.append((srcname, dstname, str(why)))
        # catch the Error from the recursive copytree so that we can
        # continue with other files
        except shutil.Error as err:
            errors.extend(err.args[0])
    try:
        shutil.copystat(src, dst)
    except OSError as why:
        errors.extend((src, dst, str(why)))
    if errors:
        raise shutil.Error(errors)
