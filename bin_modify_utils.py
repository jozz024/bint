import json
import random
import re
from base64 import b64decode, b64encode
from datetime import datetime

from amiibo import AmiiboMasterKey

from dicts import (SECTIONS, SKILLSLOTS, SPIRITSKILLS, SPIRITSKILLTABLE,
                   TRANSLATION_TABLE_CHARACTER_TRANSPLANT)
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

    def shuffle_sn(self):
        serial_number = "04"
        while len(serial_number) < 20:
            temp_sn = hex(random.randint(0, 255))
            # removes 0x prefix
            temp_sn = temp_sn[2:]
            # creates leading zero
            if len(temp_sn) == 1:
                temp_sn = '0' + temp_sn
            serial_number += ' ' + temp_sn
        return serial_number

    def rename(self, new_name, data):
        dump = self.open_dump(data)
        dump.unlock()
        dump.amiibo_nickname = new_name
        dump.lock()
        return dump.data


class Transplant(BinUtils):
    def __init__(self):
        super().__init__()

    def open_dump(self, dump):
        return super().open_dump(dump)

    def shuffle_sn(self):
        return super().shuffle_sn()

    def transplant(self, character_name, data):
        character_json = open('assets/characters.json')
        characters = json.load(character_json)
        dump = self.open_dump(data)
        dump.unlock()
        for character in characters['characters']:
            for name, namelist in character.items():
                if character_name.title() == name:
                    dump.data[84:92] = bytes.fromhex(namelist[0])
                    dump.lock()
                    dump.data = self.shuffle_sn(dump.data)
                    return dump.data
                elif character_name.lower().replace(' ', '') in TRANSLATION_TABLE_CHARACTER_TRANSPLANT:
                    if TRANSLATION_TABLE_CHARACTER_TRANSPLANT[character_name.lower().replace(' ', '')].title() == name:
                        dump.data[84:92] = bytes.fromhex(namelist[0])
                        dump.lock()
                        dump.uid_hex = self.shuffle_sn()
                        return dump.data
        raise KeyError


class Spirits(BinUtils):
    def __init__(self):
        super().__init__()

    def open_dump(self, dump):
        return super().open_dump(dump)

    def validate_skill(self, skill):
        if skill in SPIRITSKILLTABLE:
            skill_id = SPIRITSKILLS[SPIRITSKILLTABLE[skill]]
            return skill_id, SPIRITSKILLTABLE[skill]
        else:
            skill_id = SPIRITSKILLS[skill]
        return skill_id, skill

    def validate_loadout(self, attack, defense, skill_1, skill_2, skill_3):
        maxstats = 5000
        slotsfilled = (
            SKILLSLOTS[skill_1.lower()]
            + SKILLSLOTS[skill_2.lower()]
            + SKILLSLOTS[skill_3.lower()]
        )
        if slotsfilled == 1:
            maxstats = maxstats - 300
        if slotsfilled == 2:
            maxstats = maxstats - 500
        if slotsfilled == 3:
            maxstats = maxstats - 800
        if attack + defense <= maxstats:
            return None
        else:
            raise IndexError

    def set_spirits(self, data, attack: int, defense: int, skill_1_name, skill_2_name, skill_3_name):
        skill_1, skill_1_name = self.validate_skill(skill_1_name)
        skill_2, skill_2_name = self.validate_skill(skill_2_name)
        skill_3, skill_3_name = self.validate_skill(skill_3_name)
        dump = AmiiboDump(self.keys, data)
        dump.unlock()
        self.validate_loadout(attack, defense, skill_1_name, skill_2_name, skill_3_name)
        dump.data[0x1A4:0x1A6] = attack.to_bytes(2, "little")
        dump.data[0x1A6:0x1A8] = defense.to_bytes(2, "little")
        dump.data[0x140:0x141] = skill_1.to_bytes(1, "little")
        dump.data[0x141:0x142] = skill_2.to_bytes(1, "little")
        dump.data[0x142:0x143] = skill_3.to_bytes(1, "little")
        dump.lock()
        return dump.data

class Ryujinx(BinUtils):
    def __init__(self):
        super().__init__()

    def open_dump(self, dump):
        return super().open_dump(dump)

    def shuffle_sn(self):
        return super().shuffle_sn()

    def bin_to_json(self, data):
        basejson = {}
        dump = self.open_dump(data)
        dump.unlock()
        basejson['FileVersion'] = 0
        basejson['Name'] = dump.amiibo_nickname
        basejson['TagUuid'] = b64encode(dump.data[0x0:0x08]).decode('ASCII')
        basejson['AmiiboId'] = dump.data[84:92].hex()
        basejson['FirstWriteDate'] = datetime.now().isoformat()
        basejson['LastWriteDate'] = datetime.now().isoformat()
        basejson['WriteCounter'] = dump.write_counter
        basejson['ApplicationAreas'] = [
            {
                "ApplicationAreaId": int(dump.app_id.hex(), 16),
                "ApplicationArea": b64encode(dump.app_area).decode('ASCII'),
            }
        ]
        return json.dumps(basejson, indent=4)

    def json_to_bin(self, ryujinx_json):
        ryujinx_json = json.loads(ryujinx_json)
        dump = self.generate_bin()
        if 'Name' in ryujinx_json:
            dump.amiibo_nickname = ryujinx_json['Name']
        dump.data[84:92] = bytes.fromhex(ryujinx_json['AmiiboId'])
        dump.write_counter = ryujinx_json['WriteCounter']
        dump.app_id = ryujinx_json['ApplicationAreas'][0]['ApplicationAreaId'].to_bytes(4, 'big')
        dump.app_area = b64decode(ryujinx_json['ApplicationAreas'][0]['ApplicationArea'])
        dump.lock()
        return dump.data

class Evaluate(BinUtils):
    def __init__(self):
        super().__init__()

    def open_dump(self, dump):
        return super().open_dump(dump)

    def getBits(self, number, bit_index, number_of_bits):
        # clears bits we don't care about
        inv_number = 255 - (number & ~(2**number_of_bits-1 << bit_index))

        return (number & inv_number) >> bit_index

    def concatonateBits(self, left, right, right_size):
        # can't use right.bit_length() because of cases where right is 0 but is 2 bits
        left = left << right_size
        return left | right


    def bineval(self, data):
        dump = self.open_dump(data)
        dump.unlock()
        bits_left = 8
        current_index = 444
        output = ""
        for sections in SECTIONS:
            section = SECTIONS[sections]
            if bits_left >= section:
                value = self.getBits(dump.data[current_index], 8 - bits_left, section)
                bits_left -= section
            else:
                value = self.getBits(dump.data[current_index], 8 - bits_left, bits_left)
                current_index += 1
                bits_requested = section - bits_left
                while bits_requested != 0:
                    if bits_requested < 8:
                        value = self.concatonateBits(self.getBits(dump.data[current_index], 0, bits_requested), value, section-bits_requested)
                        bits_left = 8 - bits_requested
                        bits_requested = 0
                    else:
                        value = self.concatonateBits(self.getBits(dump.data[current_index], 0, 8), value, bits_left)
                        current_index += 1
                        bits_left = 8
                        bits_requested -= 8

            if bits_left == 0:
                bits_left = 8
                current_index += 1

            output += f"{sections}: {value/(2**section-1)*100}\n"
        return f"```{output}```"

class NFCTools(BinUtils):
    def __init__(self):
        super().__init__()

    def open_dump(self, dump):
        return super().open_dump(dump)

    def txt_to_bin(self, txt):
        export_string_lines = None
        hex = ""
        file = str(txt, 'utf-8')
        export_string_lines = file.splitlines()

        for line in export_string_lines:
            match = re.search(r"(?:[A-Fa-f0-9]{2}:){3}[A-Fa-f0-9]{2}", line)
            if match:
                hex = hex + match.group(0).replace(":", "")

        bin = bytes.fromhex(hex)

        return bin

# binutils = NFCTools()
#
# with open('test.txt', 'rb') as test:
#     bin = binutils.txt_to_bin(test.read())
# with open('test2.bin', 'wb') as test:
#     test.write(bin)