import requests, json, yaml, os, sys, shutil, time
import logging, traceback, time, base64
import tarfile, re
import subprocess, traceback

from . import func

class PCILogItem:
    def __init__(self, time, name, content):
        self.time = time
        self.name = name
        self.content = content
    
    def __str__(self):
        return "{:.3} [{}] {}".format(self.time, self.name, self.content)
    
    def to_dict(self):
        return dict(time=self.time, name=self.name, content=self.content)

class PCILog:
    def __init__(self, name):
        self.log = []
        self.abs_time = time.time()
        self.name = name
    
    def append(self, val):
        self.log.append(PCILogItem(time.time() - self.abs_time, self.name, val))
    
    def to_json(self):
        return json.dumps(self.to_array())
    
    def to_array(self):
        rlog = []
        for l in self.log:
            rlog.append(l.to_dict())
        return rlog
    
    def merge(self, _log):
        timesft = _log.abs_time - self.abs_time
        for l in _log.log:
            self.log.append(PCILogItem(l.time + timesft, l.name, l.content))

    def __str__(self):
        return self.to_json()