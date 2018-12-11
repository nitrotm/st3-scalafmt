# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import print_function

import atexit, io, os, signal, subprocess, sys, time


ppid = os.getppid()

server = subprocess.Popen(["scalafmt_ng"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def cleanup(signum, frame):
  server.terminate()

signal.signal(signal.SIGTERM, cleanup)
signal.signal(signal.SIGHUP, cleanup)
signal.signal(signal.SIGPIPE, cleanup)

while server.poll() is None and ppid == os.getppid():
  time.sleep(1)

try:
  server.terminate()
  server.wait(1)
except:
  server.kill()
  server.wait()

sys.exit(server.returncode)
