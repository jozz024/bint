import json
import random

from amiibo import AmiiboMasterKey

from ssbu_amiibo import InvalidAmiiboDump
from ssbu_amiibo import SsbuAmiiboDump as AmiiboDump


class BinUtils:
    def __init__(self):
        with open('assets/key_retail.bin', 'rb') as keys:
            self.keys = AmiiboMasterKey.from_combined_bin(keys.read())

    def open_dump(self, dump):
        """Opens the given data in the AmiiboDump class.

        Args:
            dump (bytes): A bytes-like object.

        Raises:
            InvalidAmiiboDump: Raises InvalidAmiiboDump if it cannot load the data.

        Returns:
            AmiiboDump: Dump of the given data.
        """
        bin_dump = dump
        if len(bin_dump) == 540:
            dump = AmiiboDump(self.keys, bin_dump)
            return dump
        elif 532 <= len(bin_dump) <= 572:
            while len(bin_dump) < 540:
                bin_dump += b'\x00'
            if len(bin_dump) > 540:
                bin_dump = bin_dump[:-(len(bin_dump) - 540)]
                dump = AmiiboDump(self.master_keys, bin_dump)
                return dump

        else:
            raise InvalidAmiiboDump

    def shuffle_sn(self, data):
        dump = self.open_dump(data)
        dump.unlock()
        serial_number = "04"
        while len(serial_number) < 20:
            temp_sn = hex(random.randint(0, 255))
            # removes 0x prefix
            temp_sn = temp_sn[2:]
            # creates leading zero
            if len(temp_sn) == 1:
                temp_sn = '0' + temp_sn
            serial_number += ' ' + temp_sn
        dump.uid_hex = serial_number
        dump.lock()
        return dump.data


class Transplant(BinUtils):
    def __init__(self):
        super().__init__()

    def __open_dump(self, dump):
        return super().open_dump(dump)

    def shuffle_sn(self, data):
        return super().shuffle_sn(data)

    def transplant(self, character_name, data):
        character_json = open('assets/characters.json')
        characters = json.load(character_json)
        dump = self.__open_dump(data)
        dump.unlock()
        for character in characters['characters']:
            for name, namelist in character.items():
                if name == character_name.title():
                    dump.data[84:92] = bytes.fromhex(namelist[0])
        dump.lock()
        dump.data = self.shuffle_sn(dump.data)
        return dump.data

# binutils = Transplant()
# with open('test.bin', 'rb') as test:
#     bin = binutils.transplant('Mario', test.read())
# with open('test.bin', 'wb') as test:
#     test.write(bin)
