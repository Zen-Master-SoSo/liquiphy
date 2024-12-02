#  liquiphy/__init__.py
#
#  Copyright 2024 liyang <liyang@veronica>
#
"""
Interface with LiquidSFZ. To see availeble commnds:

	with LiquidSFZ(filename) as liquid:
		print(dir(liquid))
		print(liquid.help())

"""
import subprocess, io, os, re, logging
from functools import partial
from signal import signal, SIGINT, SIGTERM
from good_logging import log_error

PROMPT		= 'liquidsfz> '
HELP_REGEX	= '^(\w+)\s([^\-]+)\-\s(.*)'
USAGE_ERR	= 'Usage: LiquidSFZ.%s(%s) # %s'

class LiquidSFZ:

	def __init__(self):
		signal(SIGINT, self._system_signal)
		signal(SIGTERM, self._system_signal)
		self.stay_alive = True
		self.process = subprocess.Popen(
			[ "liquidsfz", os.path.join(os.path.dirname(__file__), "empty.sfz") ],
			encoding="ASCII",
			stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
		self.read_response()
		self.write('help')
		for line in self.read_response().split("\n"):
			m = re.match(HELP_REGEX, line)
			if m:
				args = m[2].strip()
				tup = (
					m[1],
					args.split(' ') if args else [],
					m[3]
				)
				setattr(self, tup[0], partial(self._exec, tup))

	def _exec(self, funcsig, /, *args):
		if len(funcsig[1]) != len(args):
			raise UsageError(USAGE_ERR %
				(funcsig[0], ", ".join(funcsig[1]), funcsig[2]))
		self.write(funcsig[0] + " " + " ".join([ str(arg) for arg in args]))
		return self.read_response()

	def write(self, command):
		logging.debug('Writing "%s"' % command)
		self.process.stdin.write(command + os.linesep)
		self.process.stdin.flush()

	def read_response(self):
		logging.debug('Reading response')
		buf = io.StringIO()
		line = str()
		while self.stay_alive:
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

	def __enter__(self):
		return self

	def __exit__(self, *_):
		self._terminate()

	def _system_signal(self, *_):
		logging.debug('Caught signal - shutting down')
		self._terminate()

	def _terminate(self):
		self.process.terminate()
		self.stay_alive = False

class UsageError(Exception):
	pass


if __name__ == "__main__":
	from pprint import pprint
	log_format = "[%(filename)24s:%(lineno)4d] %(levelname)-8s %(message)s"
	logging.basicConfig(level = logging.DEBUG, format = log_format)

	with LiquidSFZ() as liquid:
		pprint([ att for att in dir(liquid) if att[0] != '_' ])
		print(liquid.info())
		print(liquid.max_voices(8))
		print(liquid.info())
		try:
			liquid.help('bad arg', 'another')
		except UsageError as e:
			log_error(e)
		try:
			liquid.gain()
		except UsageError as e:
			log_error(e)
		print(liquid.help())

#  end liquiphy/__init__.py
