#!/usr/bin/python
import sys,os,os.path,re,time,subprocess,syslog
from glob import glob
from getopt import getopt, GetoptError

CFMOUNT = "/nodeconf/fs"
CHEF_INIT = "chef-init.json"
EXEC_INIT = "init.sh"
FLAG_FILE = "/etc/nodeconf-finished"
VFAT_LABEL = "NODECONF"

syslog.openlog("nodeconf")

def msg(s):
    print "*** ERROR: %s" % s
    syslog.syslog("*** ERROR: %s" % s)

def err(s):
    msg(s)
    sys.exit(1)

def help():
    print "This script will attempt to locate a drive / partition among /dev/sd*"
    print "which contains a file system of type vfat with the label \"%s\"." % VFAT_LABEL
    print "If found, the script first checks if there is a file named %s in its root" % EXEC_INIT
    print "and executes it if it exists. Next, the script checks if there is"
    print "a file named %s. If this file exists, it will be passed to chef-solo" % CHEF_INIT
    print "for execution." 

if len(sys.argv) > 1:
    try:
        opts, args = getopt(sys.argv[1:], "h")
    except GetoptError as err:
        print "Invalid arguments."
    for o,a in opts:
        if o == "-h":
            help()
            sys.exit(0)
        else:
            assert False, "unknown option: %s" % o

if os.path.exists(FLAG_FILE):
    sys.exit(0)

if os.getuid() != 0:
    err("This utility needs to be run as root")

re_label = re.compile(r"""label: "(\w+)\s*""", re.I)
found_drive = None
for drive in glob("/dev/sd*"):
    descr = subprocess.check_output(["/usr/bin/file", "-s", drive])
    m = re_label.search(descr)
    if m != None:
        if m.group(1) == VFAT_LABEL:
            print "Found apparent node configuration drive at", drive
            found_drive = drive
            break

if found_drive == None:
    err("Cannot find a configuration drive")

if not os.path.isdir(CFMOUNT):
    os.mkdirs(CFMOUNT)

if subprocess.call(["/bin/mount", found_drive, CFMOUNT]) != 0:
    err("Cannot mount found drive on %s" % CFMOUNT)

os.chdir(CFMOUNT)

execs = 0
if os.path.exists(EXEC_INIT):
    os.system("./%s | tee /var/log/%s.log" % (EXEC_INIT, EXEC_INIT))
    execs += 1

if os.path.exists(CHEF_INIT):
    os.system("chef-solo -j %s | tee /var/log/%s.log" % (CHEF_INIT, CHEF_INIT))
    execs += 1

if execs == 0:
    msg("nodeconf: nothing executed")

file(FLAG_FILE, "w").write("%d\n" % time.time())

os.chdir("/")
os.system("umount -f %s" % CFMOUNT)

