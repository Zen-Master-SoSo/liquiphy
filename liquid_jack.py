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
import logging
from liquiphy import LiquidSFZ
from jack import Client

JACK_NAME	= 'liquidjack'


class LiquidJack(LiquidSFZ):
	"""
	LiquidSFZ client with added Jack audio tools functionality.
	"""

	midi_in = None
	audio_out_1 = None
	audio_out_2 = None

	def __init__(self, filename = None):
		self.client = Client(JACK_NAME, no_start_server=True)
		self.client.set_port_registration_callback(self.port_registration_callback)
		self.client.activate()
		super().__init__(filename)

	def port_registration_callback(self, port, register):
		"""
		Called by Jack when port is added or removed
		"""
		if register and 'liquidsfz' in port.name:
			if port.is_midi and self.midi_in is None:
				self.midi_in = port
			elif 'audio_out_1' in port.name and self.audio_out_1 is None:
				self.audio_out_1 = port
			elif 'audio_out_2' in port.name and self.audio_out_2 is None:
				self.audio_out_2 = port


if __name__ == "__main__":
	from pprint import pprint
	log_format = "[%(filename)24s:%(lineno)4d] %(levelname)-8s %(message)s"
	logging.basicConfig(level = logging.DEBUG, format = log_format)

	with LiquidJack() as liquid:
		pprint([ att for att in dir(liquid) if att[0] != '_' ])
		print(liquid.midi_in)
		print(liquid.audio_out_1)
		print(liquid.audio_out_2)

#  end liquiphy/__init__.py
