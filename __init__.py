#  liquiphy/__init__.py
#
#  Copyright 2024 liyang <liyang@veronica>
#
"""
Interface with LiquidSFZ. To see available commnds:

	with LiquidSFZ(filename) as liquid:
		print(dir(liquid))
		print(liquid.help())

"""
import subprocess, io, os, re, logging
from functools import partial
from threading import Thread
from queue import Queue, Empty

PROMPT		= 'liquidsfz> '
HELP_REGEX	= '^(\w+)\s([^\-]+)\-\s(.*)'
USAGE_ERR	= 'Usage: LiquidSFZ.%s(%s) # %s'


class LiquidSFZ:

	def __init__(self, filename = None, defer_start = False):
		self.filename = os.path.join(os.path.dirname(__file__), "empty.sfz") \
			if filename is None else filename
		if not defer_start:
			self.start()

	def start(self):
		self.process = subprocess.Popen(
			[ "liquidsfz", self.filename ],
			encoding="ASCII",
			stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
		self.stderr_queue = Queue()
		Thread(target = self._read_stderr, daemon = True).start()
		self.read_response()
		self.write('help')
		for line in self.read_response().split(os.linesep):
			m = re.match(HELP_REGEX, line)
			if m:
				args = m[2].strip()
				funcsig = (
					m[1],
					args.split(' ') if args else [],
					m[3]
				)
				setattr(self, funcsig[0], partial(self._exec, funcsig))

	def _exec(self, funcsig, /, *args):
		if len(funcsig[1]) != len(args):
			raise UsageError(USAGE_ERR %
				(funcsig[0], ", ".join(funcsig[1]), funcsig[2]))
		self.write(funcsig[0] + " " + " ".join(str(arg) for arg in args))
		return self.read_response()

	def write(self, command):
		"""
		Send a command to the liquidsfz instance running in a subprocess.
		This function is normally used internally and not called from outside.
		"""
		self.process.stdin.write(command + os.linesep)
		self.process.stdin.flush()

	def read_response(self):
		"""
		Read the response from the liquidsfz instance running in a subprocess.
		This function is normally used internally and not called from outside.
		"""
		buf = io.StringIO()
		line = str()
		while True:
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
		Return the (str) content of the liquidsfz instance's stderr as an list of lines.
		"""
		lines = []
		while True:
			try:
				lines.append(self.stderr_queue.get_nowait())
			except Empty:
				return lines

	def __enter__(self):
		return self

	def __exit__(self, *_):
		self.quit()


class UsageError(Exception):
	pass


#  end liquiphy/__init__.py
