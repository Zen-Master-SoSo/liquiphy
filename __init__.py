#  liquiphy/__init__.py
#
#  Copyright 2024 liyang <liyang@veronica>
#
import subprocess, io, os, logging
from time import sleep
from signal import signal, SIGINT, SIGTERM


class LiquidSFZ:

	def __init__(self):
		signal(SIGINT, self.system_signal)
		signal(SIGTERM, self.system_signal)
		self.process = subprocess.Popen(
			["liquidsfz", "/mnt/data-drive/docs/sfz/Drumsets/Pearl-Masters/Pearl.sfz"],
			encoding="ASCII",
			stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
		self.stay_alive = True
		self.read_response()
		self.write("help\n")
		self.read_response()
		self.write("quit\n")
		while self.process.poll() is None:
			logging.debug('waiting')
			sleep(.5)

	def write(self, stuff):
		logging.debug('Writing "%s"' % stuff.rstrip())
		self.process.stdin.write(stuff)
		self.process.stdin.flush()

	def read_response(self):
		logging.debug('Reading response')
		buf = io.StringIO()
		line = ''
		while self.stay_alive:
			char = self.process.stdout.read(1)
			buf.write(char)
			if char == os.linesep:
				line = ''
			else:
				line = line + char
			if line == 'liquidsfz> ':
				logging.debug('Got "liquidsfz> " prompt - break')
				break
		logging.debug('Done reading')
		buf.seek(0)
		print(buf.read())

	def system_signal(self, sig, frame):
		logging.debug("Caught signal - shutting down")
		self.process.terminate()
		self.stay_alive = False


log_level = logging.DEBUG
log_format = "[%(filename)24s:%(lineno)4d] %(levelname)-8s %(message)s"
logging.basicConfig(level = log_level, format = log_format)

LiquidSFZ()

#  end liquiphy/__init__.py
