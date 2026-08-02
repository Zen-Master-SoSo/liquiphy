#  liquiphy/__init__.py
#
#  Copyright 2024-2026 Leon Dionne <ldionne@dridesign.sh.cn>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
"""
A quick and dirty interface to the liquidsfz command-line using python's subprocess.

To see available commnds:

	with LiquidSFZ(filename) as liquid:
		print(dir(liquid))
		print(liquid.help())

"""
import subprocess, io, os, logging
from re import compile as rcompile
from functools import partial
from threading import Thread
from queue import Queue, Empty

__version__ = "1.3.0"

PROMPT		= 'liquidsfz> '
HELP_REGEX	= rcompile(r'^(\w+)\s([^\-]+)\-\s(.*)')
USAGE_ERR	= 'Usage: LiquidSFZ.%s(%s) # %s'


class LiquidSFZ:

	def __init__(self, filename = None, defer_start = False):
		self.filename = os.path.join(os.path.dirname(__file__), "empty.sfz") \
			if filename is None else filename
		self.started = False
		if not defer_start:
			self.start()

	def start(self):
		self.process = subprocess.Popen(
			[ "liquidsfz", self.filename ],
			encoding = "ASCII",
			stdout = subprocess.PIPE, stdin = subprocess.PIPE, stderr = subprocess.PIPE)
		self.stderr_queue = Queue()
		Thread(target = self._read_stderr, daemon = True).start()
		self.read_response()
		self.started = True

	def help(self):
		"""
		show this help
		"""
		self.write(f"help")
		return self.read_response()

	def quit(self):
		"""
		quit liquidsfz
		"""
		self.write(f"quit")
		return self.read_response()

	def load(self, sfz_filename):
		"""
		load sfz from filename
		"""
		self.write(f"load {sfz_filename}")
		return self.read_response()

	def allsoundoff(self):
		"""
		stop all sounds
		"""
		self.write(f"allsoundoff")
		return self.read_response()

	def reset(self):
		"""
		system reset (stop all sounds, reset controllers)
		"""
		self.write(f"reset")
		return self.read_response()

	def noteon(self, chan, key, vel):
		"""
		start note
		"""
		self.write(f"noteon {chan} {key} {vel}")
		return self.read_response()

	def noteoff(self, chan, key):
		"""
		stop note
		"""
		self.write(f"noteoff {chan} {key}")
		return self.read_response()

	def cc(self, chan, ctrl, value):
		"""
		send controller event
		"""
		self.write(f"cc {chan} {ctrl} {value}")
		return self.read_response()

	def pitch_bend(self, chan, val):
		"""
		send pitch bend event (0 <= val <= 16383)
		"""
		self.write(f"pitch_bend {chan} {val}")
		return self.read_response()

	def gain(self, value):
		"""
		set gain (0 <= value <= 5)
		"""
		self.write(f"gain {value}")
		return self.read_response()

	def max_voices(self, value):
		"""
		set maximum number of voices
		"""
		self.write(f"max_voices {value}")
		return self.read_response()

	def max_cache_size(self, size):
		"""
		set maximum cache size in MB
		"""
		self.write(f"max_cache_size {size}")
		return self.read_response()

	def preload_time(self, time):
		"""
		set preload time in ms
		"""
		self.write(f"preload_time {time}")
		return self.read_response()

	def keys(self):
		"""
		show keys supported by the sfz
		"""
		self.write(f"keys")
		return self.read_response()

	def switches(self):
		"""
		show switches supported by the sfz
		"""
		self.write(f"switches")
		return self.read_response()

	def ccs(self):
		"""
		show ccs supported by the sfz
		"""
		self.write(f"ccs")
		return self.read_response()

	def stats(self):
		"""
		show voices/cache/cpu usage
		"""
		self.write(f"stats")
		return self.read_response()

	def info(self):
		"""
		show information
		"""
		self.write(f"info")
		return self.read_response()

	def voice_count(self):
		"""
		print number of active synthesis voices
		"""
		self.write(f"voice_count")
		return self.read_response()

	def sleep(self, time_ms):
		"""
		sleep for some milliseconds
		"""
		self.write(f"sleep {time_ms}")
		return self.read_response()

	def source(self, filename):
		"""
		load a file and execute each line as command
		"""
		self.write(f"source {filename}")
		return self.read_response()

	def echo(self, text):
		"""
		print text
		"""
		self.write(f"echo {text}")
		return self.read_response()

	def write(self, command):
		"""
		Send a command to the liquidsfz instance running in a subprocess.
		This function is normally used internally and not called from outside.
		"""
		if self.started:
			self.process.stdin.write(command + os.linesep)
			self.process.stdin.flush()

	def read_response(self):
		"""
		Read the response from the liquidsfz instance running in a subprocess.
		This function is normally used internally and not called from outside.
		"""
		buf = io.StringIO()
		line = str()
		while self.started:
			if self.process.poll() is not None:
				if self.process.returncode:
					logging.warning('liquidsfz terminated with exit code %d',
						self.process.returncode)
				return None
			char = self.process.stdout.read(1)
			if char == os.linesep:
				buf.write(line)
				buf.write(char)
				line = str()
			else:
				line += char
			if line == PROMPT:
				break
		buf.seek(0)
		return buf.read()

	def _read_stderr(self):
		for line in iter(self.process.stderr.readline, b''):
			self.stderr_queue.put(line.strip())

	def stderr(self):
		"""
		Return the (str) content of the liquidsfz instance's stderr as a single string,
		with each line separated by the os' line separator.
		"""
		return os.linesep.join(self.stderr_lines())

	def stderr_lines(self):
		"""
		Generator which yields the (str) content of the liquidsfz instance's stderr.
		"""
		while True:
			try:
				yield self.stderr_queue.get_nowait()
			except Empty:
				break

	def __enter__(self):
		return self

	def __exit__(self, *_):
		self.quit()


#  end liquiphy/__init__.py
