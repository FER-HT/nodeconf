#!/usr/bin/python
import sys,os,os.path,re,time,subprocess,syslog
from glob import glob

CFMOUNT = "/nodeconf/fs"

syslog.openlog("nodeconf")

def err(msg):
    print "*** ERROR: %s" % msg
    syslog.syslog("*** ERROR: %s" % msg)
    sys.exit(1)

if os.getuid() != 0:
    err("This utility needs to be run as root")

re_label = re.compile(r"""label: "(\w+)\s*""", re.I)
found_drive = None
for drive in glob("/dev/sd*"):
    descr = subprocess.check_output(["/usr/bin/file", "-s", drive])
    m = re_label.search(descr)
    if m != None:
        if m.group(1) == "NODECONF":
            print "Found apparent node configuration drive at", drive
            found_drive = drive
            break

if found_drive == None:
    err("Cannot find a configuration drive")

if not os.path.isdir(CFMOUNT):
    os.mkdir(CFMOUNT)

if subprocess.call(["/bin/mount", found_drive, CFMOUNT]) != 0:
    err("Cannot mount found drive on %s" % CFMOUNT)


