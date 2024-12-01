#  liquiphy/__init__.py
#
#  Copyright 2024 liyang <liyang@veronica>
#
"""
Interface with LiquidSFZ. To see availeble commnds:

	with LiquidSFZ(filename) as liquid:
		print(liquid.help())

"""
import subprocess, io, os, re, logging
from time import sleep
from signal import signal, SIGINT, SIGTERM

PROMPT = 'liquidsfz> '
HELP_REGEX = '^(\w+)\s([^\-]+)\-\s(.*)'

class LiquidSFZ:

	def __init__(self):
		signal(SIGINT, self.system_signal)
		signal(SIGTERM, self.system_signal)
		self.stay_alive = True
		self.process = subprocess.Popen(
			["liquidsfz", "/home/liyang/docs/sfz/Drumsets/Pearl-Masters/Pearl.sfz"],
			encoding="ASCII",
			stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
		self.read_response()
		self.write('help')
		helptext = self.read_response()
		commands = {
			tup[0]:tup[1:] \
			for tup in [
				self._interpret_helptext(line) \
				for line in helptext.split("\n")
				if re.match(HELP_REGEX, line)
			]
		}
		self.write('quit')
		while self.process.poll() is None:
			logging.debug('waiting')
			sleep(.2)

	def _interpret_helptext(self, line):
		m = re.match(HELP_REGEX, line)
		args = m[2].strip()
		return (
			m[1],
			args.split(' ') if args else [],
			m[3]
		)

	def write(self, command):
		logging.debug('Writing "%s"' % command)
		self.process.stdin.write(command + os.linesep)
		self.process.stdin.flush()

	def read_response(self):
		logging.debug('Reading response')
		buf = io.StringIO()
		line = ''
		while self.stay_alive:
			char = self.process.stdout.read(1)
			if char == os.linesep:
				buf.write(line)
				buf.write(char)
				line = ''
			else:
				line += char
			if line == PROMPT:
				logging.debug('Got "%s" prompt - break', PROMPT)
				break
		buf.seek(0)
		return buf.read()

	def __enter__(self):
		return self

	def __exit__(self, *_):
		self._terminate()

	def system_signal(self, *_):
		logging.debug("Caught signal - shutting down")
		self._terminate()

	def _terminate(self):
		self.process.terminate()
		self.stay_alive = False


log_level = logging.DEBUG
log_format = "[%(filename)24s:%(lineno)4d] %(levelname)-8s %(message)s"
logging.basicConfig(level = log_level, format = log_format)

with LiquidSFZ() as liquid:
	print(liquid.help())

#  end liquiphy/__init__.py
