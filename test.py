#  liquiphy/test.py
#
#  Copyright 2025 liyang <liyang@veronica>
#
import sys, logging
from pprint import pprint
from good_logging import log_error
from liquiphy import LiquidSFZ, UsageError

if __name__ == "__main__":
	log_format = "[%(filename)24s:%(lineno)4d] %(levelname)-8s %(message)s"
	logging.basicConfig(level = logging.DEBUG, format = log_format)

	with LiquidSFZ() as liquid:
		print('******** Attributes:')
		pprint([ att for att in dir(liquid) if att[0] != '_' ])
		print('******** Info:')
		print(liquid.info())
		print('******** Set max_voices to 8 ...')
		print(liquid.max_voices(8))
		print('******** Info:')
		print(liquid.info())

		try:
			print('******** Send bad command ...')
			liquid.bad_command()
		except AttributeError as e:
			log_error(e)

		try:
			print('******** Send bad argument ...')
			liquid.help('bad argument')
		except UsageError as e:
			log_error(e)

		try:
			print('******** Send incomplete arguments ...')
			liquid.gain()
		except UsageError as e:
			log_error(e)

#  end liquiphy/test.py
