#  liquiphy/dev/create_funcs.py
#
#  Copyright 2026 Leon Dionne <ldionne@dridesign.sh.cn>
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
Writes the functions from liquidsfz help.
"""
import logging, sys, subprocess, liquiphy
from os import linesep
from io import StringIO
from pathlib import Path
from threading import Thread
from re import compile as rcompile

PROMPT		= 'liquidsfz> '
HELP_REGEX	= rcompile(r'^(\w+)\s([^\-]+)\-\s(.*)')
USAGE_ERR	= 'Usage: LiquidSFZ.%s(%s) # %s'


class FuncMaker:

	def __init__(self):
		self.process = subprocess.Popen(
			[ "liquidsfz", str(Path(liquiphy.__file__).parent / 'empty.sfz') ],
			encoding = "ASCII",
			stdout = subprocess.PIPE, stdin = subprocess.PIPE, stderr = subprocess.PIPE)
		Thread(target = self.read_stderr, daemon = True).start()
		self.read_response()

	def make(self):
		self.write('help')
		for line in self.read_response().split(linesep):
			m = HELP_REGEX.match(line)
			if m:
				func = m[1]
				args = m[2].strip()
				args = args.split(' ') if args else []
				doc = m[3]
				parms = ', '.join(['self'] + args)
				cmd = m[1] + ' {' + '} {'.join(args) + '}' if args else m[1]
				print(f"""	def {func}({parms}):
		\"\"\"
		{doc}
		\"\"\"
		self.write(f"{cmd}")
		return self.read_response()
""")

	def write(self, command):
		"""
		Send a command to the liquidsfz instance running in a subprocess.
		This function is normally used internally and not called from outside.
		"""
		self.process.stdin.write(command + linesep)
		self.process.stdin.flush()

	def read_response(self):
		"""
		Read the response from the liquidsfz instance running in a subprocess.
		This function is normally used internally and not called from outside.
		"""
		buf = StringIO()
		line = str()
		while True:
			if self.process.poll() is not None:
				if self.process.returncode:
					logging.warning('liquidsfz terminated with exit code %d',
						self.process.returncode)
				return None
			char = self.process.stdout.read(1)
			if char == linesep:
				buf.write(line)
				buf.write(char)
				line = str()
			else:
				line += char
			if line == PROMPT:
				break
		return buf.getvalue()

	def read_stderr(self):
		for line in iter(self.process.stderr.readline, b''):
			sys.stderr.write(line)


def main():
	logging.basicConfig(
		level=logging.DEBUG,
		format="[%(filename)24s:%(lineno)3d] %(levelname)-8s %(message)s"
	)
	FuncMaker().make()


if __name__ == "__main__":
	sys.exit(main() or 0)


#  end liquiphy/dev/create_funcs.py
