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

PROMPT		= 'liquidsfz> '
HELP_REGEX	= '^(\w+)\s([^\-]+)\-\s(.*)'
USAGE_ERR	= 'Usage: LiquidSFZ.%s(%s)'

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
		helptext = self.read_response()
		for tup in [
			self._interpret_helptext(line) \
			for line in helptext.split("\n")
			if re.match(HELP_REGEX, line)
		]:
			setattr(self, tup[0], partial(self._exec, tup))

	def _interpret_helptext(self, line):
		m = re.match(HELP_REGEX, line)
		args = m[2].strip()
		return (
			m[1],
			args.split(' ') if args else [],
			m[3]
		)

	def _exec(self, funcsig, /, *args):
		if len(funcsig[1]) != len(args):
			raise UsageError(USAGE_ERR % (funcsig[0], ", ".join(funcsig[1])))
		self.write(funcsig[0] + " " + " ".join(args))
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
		logging.debug("Caught signal - shutting down")
		self._terminate()

	def _terminate(self):
		self.process.terminate()
		self.stay_alive = False

class UsageError(Exception):
	pass

def log_error(e):
	tb = e.__traceback__
	logging.error('%s %s(), line %s: %s "%s"',
		os.path.basename(tb.tb_frame.f_code.co_filename),
		tb.tb_frame.f_code.co_name,
		tb.tb_lineno,
		type(e).__name__,
		str(e),
	)

if __name__ == "__main__":
	log_level = logging.DEBUG
	log_format = "[%(filename)24s:%(lineno)4d] %(levelname)-8s %(message)s"
	logging.basicConfig(level = log_level, format = log_format)

	with LiquidSFZ() as liquid:
		print(dir(liquid))
		try:
			liquid.help('bad arg', 'another')
		except UsageError as e:
			log_error(e)
		print(liquid.help())

#  end liquiphy/__init__.py
