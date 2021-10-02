import subprocess
import os

trepo = "nemo:testing:hw:{0}:{1}".format(os.environ["VENDOR"],os.environ["DEVICE"])
drepo = "nemo:devel:hw:{0}:{1}".format(os.environ["VENDOR"],os.environ["DEVICE"])

cmd = "osc ls {0}".format(drepo)
process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, text=True)
packages = process.communicate()[0]

for p in packages.split('\n'):
    p = p.strip()
    if p == '' or p[0] == '#' or p == "_pattern":
        continue
    print("osc -A https://api.sailfishos.org copypac {0} {1} {2}".format(drepo,p,trepo))

