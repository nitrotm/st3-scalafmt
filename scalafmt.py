# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import print_function

import atexit, io, multiprocessing, os, subprocess, socket, sys, time

import sublime, sublime_plugin


PLUGIN_PATH = os.path.join(sublime.packages_path(), os.path.dirname(os.path.realpath(__file__)))
PLUGIN_NAME = 'Scalafmt'
PLUGIN_CMD_NAME = 'scalafmt_run'


def st_status_message(msg):
  sublime.set_timeout(lambda: sublime.status_message('{0}: {1}'.format(PLUGIN_NAME, msg)), 0)

def st_get_project_path():
  """Get the active Sublime Text project path.
  Original: https://gist.github.com/astronaughts/9678368
  :rtype: object
  :return: The active Sublime Text project path.
  """
  window = sublime.active_window()
  folders = window.folders()
  if len(folders) == 1:
    return folders[0]
  else:
    active_view = window.active_view()
    if active_view:
      active_file_name = active_view.file_name()
    else:
      active_file_name = None
    if not active_file_name:
      return folders[0] if len(folders) else os.path.expanduser('~')
    for folder in folders:
      if active_file_name.startswith(folder):
        return folder
  return os.path.dirname(active_file_name)

def try_find_config(filename):
  root = st_get_project_path()
  current = os.path.abspath(os.path.dirname(filename))
  while current.startswith(root):
    config = os.path.join(current, '.scalafmt.conf')
    if os.path.isfile(config):
      return config
    current = os.path.dirname(current)
  return None


class Formatter(object):
  def __init__(self):
    self.server = None

  def format(self, source, filename=None, config=None, timeout=30):
    if not self.is_ready() and not self.spawn():
      return ("cannot start nailgun daemon", None)

    params = ['ng', 'org.scalafmt.cli.Cli', '--non-interactive', '--stdin', '--stdout']
    if config is not None:
      params.append('--config')
      params.append(config)
    if filename is not None:
      params.append('--assume-filename')
      params.append(filename)

    st_status_message('formatting code...')
    task = subprocess.Popen(params, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out = ''
    err = ''
    try:
      stdout, stderr = task.communicate(bytes(source, 'utf-8'), timeout)
      out = str(stdout, 'utf-8')
      err = str(stderr, 'utf-8').strip()
    except subprocess.TimeoutExpired:
      task.kill()
    task.wait()
    if task.returncode == 0 and len(err) == 0:
      return (None, out)
    return ("formatting failed (code %d)" % (task.returncode), err)

  def is_ready(self, delay=0):
    start = time.time()
    while delay == 0 or (time.time() - start) <= delay:
      try:
        s = socket.create_connection(('localhost', 2113), delay)
        s.close()
        return True
      except:
        if delay <= 0:
          break
      time.sleep(0.1)
    return False

  def spawn(self, delay=2):
    self.terminate()
    st_status_message('spawning nailgun deamon...')
    script = sublime.load_resource('Packages/ScalafmtEnhanced/scripts/nailgun.py')
    self.server = subprocess.Popen(
      [sys.executable or 'python3'],
      stdin=subprocess.PIPE,
      stdout=None,
      stderr=None
    )
    self.server.stdin.write(bytes(script, 'utf-8'))
    self.server.stdin.close()
    if not self.is_ready(delay):
      self.terminate()
      st_status_message('nailgun deamon cannot be started')
      return False
    st_status_message('nailgun deamon ready')
    return True

  def terminate(self):
    if self.server is None:
      return
    self.server.terminate()
    self.server.wait();
    self.server = None


formatter = Formatter()

def plugin_unloaded():
  formatter.terminate()


class ScalafmtRun(sublime_plugin.TextCommand):
  def is_visible(self):
    filename = self.view.file_name()
    if not filename:
      syntax = self.view.settings().get('syntax')
      return syntax.lower().find('scala') >= 0
    return filename and filename.endswith('.scala')

  def is_enabled(self):
    return self.is_visible()

  def description(self):
    return 'Format scala code using scalafmt'

  def run(self, edit, save_file=False, config=None):
    if not self.is_visible():
      return

    filename = self.view.file_name()
    if filename is not None:
      if not config:
        config = try_find_config(filename)
      root = st_get_project_path()
      filename = os.path.abspath(filename)[len(root)+1:]

    regions = [region for region in self.view.sel() if not region.empty()]
    if save_file or len(regions) == 0:
      regions = [sublime.Region(0, self.view.size())]

    last_error = None
    logs = []
    for region in regions:
      source = self.view.substr(region)
      (error, output) = formatter.format(source, filename, config)
      if error is None:
        self.view.replace(edit, region, output)
      else:
        last_error = error
        if output and len(output) > 0:
          logs.append(output)
    if last_error is None:
      st_status_message('code formatted.')
    else:
      st_status_message(last_error)
      if len(logs) > 0:
        sublime.set_timeout(lambda: self.show('scalafmt', ''.join(['<pre>' + self.console2html(log) + '</pre>' for log in logs])))

  def show(self, title, html):
    (width, height) = self.view.viewport_extent()
    self.view.show_popup(
      '<div style="font-weight: bold">' + title + '</div>' + html,
      sublime.HIDE_ON_MOUSE_MOVE_AWAY,
      -1,
      width,
      height
    )

  def console2html(self, value):
    fg_codes = {
      '\u001B[30m': 'black',
      '\u001B[31m': 'red',
      '\u001B[32m': 'green',
      '\u001B[33m': 'yellow',
      '\u001B[34m': 'blue',
      '\u001B[35m': 'magenta',
      '\u001B[36m': 'cyan',
      '\u001B[37m': 'white',
    }
    value = value.replace('\\n', '\n')
    for (fro, to) in fg_codes.items():
      value = value.replace(fro, '<span style="color: %s;">' % to)
    value = value.replace('\u001B[0m', '</span>')
    return value


class SaveEventListener(sublime_plugin.EventListener):
  def on_pre_save(self, view):
    if not view.file_name().endswith('.scala'):
      return
    config = try_find_config(view.file_name())
    if not config:
      return
    view.run_command(PLUGIN_CMD_NAME, { 'save_file': True, 'config': config })
