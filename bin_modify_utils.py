import json
import random
import re
from base64 import b64decode, b64encode
from datetime import datetime
from bitstring import BitString

from amiibo import AmiiboMasterKey

from dicts import (SECTIONS, SKILLSLOTS, SPIRITSKILLS, SPIRITSKILLTABLE,
                   TRANSLATION_TABLE_CHARACTER_TRANSPLANT, param_defs, personality_names)
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
            if len(bin_dump) < 540:
                while len(bin_dump) < 540:
                    bin_dump += b'\x00'
                dump = AmiiboDump(self.keys, bin_dump)
                return dump
            if len(bin_dump) > 540:
                bin_dump = bin_dump[:-(len(bin_dump) - 540)]
                dump = AmiiboDump(self.keys, bin_dump)
                return dump

        else:
            raise InvalidAmiiboDump

    def shuffle_sn(self):
        """Generates a shuffled serial number for the amiibo to use.

        Returns:
            str: A string of bytes separated by spaces.
        """
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

    def rename(self, new_name: str, data: bytes):
        """Renames the given dump data.

        Args:
            new_name (str): The new name to give the amiibo.
            data (bytes): The amiibo data.

        Returns:
            bytes: The renamed amiibo.
        """
        dump = self.open_dump(data)
        dump.unlock()
        dump.amiibo_nickname = new_name
        dump.lock()
        return dump.data


class Transplant(BinUtils):
    def __init__(self):
        super().__init__()

    def open_dump(self, dump):
        """Opens the given data in the AmiiboDump class.

        Args:
            dump (bytes): A bytes-like object.

        Raises:
            InvalidAmiiboDump: Raises InvalidAmiiboDump if it cannot load the data.

        Returns:
            AmiiboDump: Dump of the given data.
        """
        return super().open_dump(dump)

    def shuffle_sn(self):
        """Generates a shuffled serial number for the amiibo to use.

        Returns:
            str: A string of bytes separated by spaces.
        """
        return super().shuffle_sn()

    def transplant(self, character_name, data):
        """Gives the amiibo a character swap.

        Args:
            character_name (str): The character to swap to.
            data (bytes): Bin data.

        Raises:
            KeyError: If it makes it that far it raises a keyerror.

        Returns:
            bytes: Bin data.
        """
        character_json = open('assets/characters.json')
        characters = json.load(character_json)
        dump = self.open_dump(data)
        dump.unlock()
        for character in characters['characters']:
            for name, namelist in character.items():
                if character_name.title() == name:
                    dump.data[84:92] = bytes.fromhex(namelist[0])
                    dump.uid_hex = self.shuffle_sn()
                    dump.lock()
                    return dump.data
                elif character_name.lower().replace(' ', '') in TRANSLATION_TABLE_CHARACTER_TRANSPLANT:
                    if TRANSLATION_TABLE_CHARACTER_TRANSPLANT[character_name.lower().replace(' ', '')].title() == name:
                        dump.data[84:92] = bytes.fromhex(namelist[0])
                        dump.uid_hex = self.shuffle_sn()
                        dump.lock()
                        return dump.data
        raise KeyError


class Spirits(BinUtils):
    def __init__(self):
        super().__init__()

    def open_dump(self, dump):
        """Opens the given data in the AmiiboDump class.

        Args:
            dump (bytes): A bytes-like object.

        Raises:
            InvalidAmiiboDump: Raises InvalidAmiiboDump if it cannot load the data.

        Returns:
            AmiiboDump: Dump of the given data.
        """
        return super().open_dump(dump)

    def validate_skill(self, skill):
        """Checks if the given skill is valid.

        Args:
            skill (str): Skill to check.

        Returns:
            int: skill id
            str: skill name
        """
        if skill in SPIRITSKILLTABLE:
            skill_id = SPIRITSKILLS[SPIRITSKILLTABLE[skill]]
            return skill_id, SPIRITSKILLTABLE[skill]
        else:
            skill_id = SPIRITSKILLS[skill]
        return skill_id, skill

    def validate_loadout(self, attack, defense, skill_1, skill_2, skill_3):
        """Validates the given spirit loadout.

        Args:
            attack (int): Attack stat.
            defense (int): Defense Stat.
            skill_1 (str): First Spirit skill.
            skill_2 (str): Second Spirit skill.
            skill_3 (str): Third Spirit skill.

        Raises:
            IndexError: Raises an index error so it doesn't keep going with the spirit setting.

        Returns:
            None: Nothing
        """
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
        """Sets the spirits of the given bin dump.

        Args:
            data (bytes): Dump data.
            attack (int): Attack stat.
            defense (int): Defense Stat
            skill_1_name (str): First Spirit skill.
            skill_2_name (str): Second Spirit skill.
            skill_3_name (str): Third Spirit skill.

        Returns:
            bytes: Dump data.
        """
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
        """Opens the given data in the AmiiboDump class.

        Args:
            dump (bytes): A bytes-like object.

        Raises:
            InvalidAmiiboDump: Raises InvalidAmiiboDump if it cannot load the data.

        Returns:
            AmiiboDump: Dump of the given data.
        """
        return super().open_dump(dump)

    def shuffle_sn(self):
        """Generates a shuffled serial number for the amiibo to use.

        Returns:
            str: A string of bytes separated by spaces.
        """
        return super().shuffle_sn()

    def gen_random_bytes(self, byte_amt: int):
        generated_bytes = ""
        while len(generated_bytes) < byte_amt * 2:
            temp_gen = hex(random.randint(0, 255))
            temp_gen = temp_gen[2:]
            if len(temp_gen) == 1:
                temp_gen = '0' + temp_gen
            generated_bytes += temp_gen
        return generated_bytes

    def generate_bin(self):
        bin = bytes.fromhex('00' * 540)
        dump = AmiiboDump(self.keys, bin, False)
        dump.uid_hex = self.shuffle_sn()
        dump.amiibo_nickname = 'AMIIBO'
        dump.data[0x09:0x0C] = bytes.fromhex('480FE0')
        dump.data[0x0C:0x10] = bytes.fromhex('F110FFEE')
        dump.data[0x10] = 0xA5
        dump.data[0x11:13] = bytes.fromhex(self.gen_random_bytes(2))
        dump.data[0x14:0x16] = bytes.fromhex('3000')
        dump.data[0x16:0x18] = bytes.fromhex(self.gen_random_bytes(2))
        dump.data[0x1A:0x1C] = bytes.fromhex(self.gen_random_bytes(2))
        dump.data[0xA0:0x100] = bytes.fromhex('03 00 00 40 EB A5 21 1A E1 FD C7 59 D0 5A A5 4D 44 0D 56 BD 21 CA 00 00 00 00 4D 00 69 00 69 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 40 40 00 00 21 01 02 68 44 18 26 34 46 14 81 12 17 68 0D 00 00 29 00 52 48 50 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 14 6C'.replace(' ', ''))
        dump.data[0x100:0x108] = bytes.fromhex('01006A803016E000')
        dump.data[0x108:0x10A] = bytes.fromhex(self.gen_random_bytes(2))
        dump.data[0x208:0x20C] = bytes.fromhex('01000FBD')
        dump.data[0x20c:0x214] = bytes.fromhex('000000045F000000')
        dump.data = dump.data[:-2]
        return dump

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
        if len(ryujinx_json['ApplicationAreas']) != 0:
            dump.app_id = ryujinx_json['ApplicationAreas'][0]['ApplicationAreaId'].to_bytes(4, 'big')
            dump.app_area = b64decode(ryujinx_json['ApplicationAreas'][0]['ApplicationArea'])
        dump.lock()
        return dump.data

class Evaluate(BinUtils):
    def __init__(self):
        super().__init__()

    def open_dump(self, dump):
        """Opens the given data in the AmiiboDump class.

        Args:
            dump (bytes): A bytes-like object.

        Raises:
            InvalidAmiiboDump: Raises InvalidAmiiboDump if it cannot load the data.

        Returns:
            AmiiboDump: Dump of the given data.
        """
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
        return f"```\n{output}```"

class NFCTools(BinUtils):
    def __init__(self):
        super().__init__()

    def open_dump(self, dump):
        """Opens the given data in the AmiiboDump class.

        Args:
            dump (bytes): A bytes-like object.

        Raises:
            InvalidAmiiboDump: Raises InvalidAmiiboDump if it cannot load the data.

        Returns:
            AmiiboDump: Dump of the given data.
        """
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

# Thanks to @xSke for providing the personality calculation code.
class Personality(BinUtils):
    def __init__(self):
        with open("assets/personality_data.json", "r") as fp:
            self.groups_data = json.load(fp)
        super().__init__()

    def open_dump(self, dump):
        return super().open_dump(dump)

    def decode_behavior_params(self, dump: AmiiboDump):
        params = {}

        # This data gets a lot simpler to read if you treat it as a bitstream
        # and then read it "in reverse" (flip the bytes, then read bits back to front = no byte swap issues)
        behavior_data = dump.data[0x1BC:0x1F6]

        bits = BitString(behavior_data[::-1])
        for name, size in param_defs[::-1]:
            val = bits.read("uint:{}".format(size))

            # even the game internals work with "out of 100" values so we'll keep doing that here
            val_max = (1 << size) - 1
            params[name] = val / val_max * 100
        return params


    def scale_value(self, param, value, flip):
        # the original code actually defines a default of 0 for "appeal", and then divides by it
        # on ARM this just results in 0, anywhere else it'll blow up ;)
        if param == "appeal":
            return 1

        # some of the "directional weight" parameters have different defaults defined in the code but none of them are ever used here so lol
        default = 50
        if flip:
            scaled = (default - value) / default
        else:
            scaled = (value - default) / default

        # since we rescale to range from -1.0 to 1.0, this means values below halfway are meaningless lol
        return max(0, min(1, scaled))


    def calculate_group_score(self, params, group):
        score = 0
        for param_data in group["scores"]:
            name = param_data["param"]
            value = self.scale_value(name, params[name], param_data["flip"])

            if value >= param_data["min_1"]:
                score += param_data["point_1"]
            if value >= param_data["min_2"]:
                score += param_data["point_2"]

        return score


    def meets_group_necessary_requirements(self, params, group):
        name = group["necessary_param"]
        if not name:
            return True

        value = self.scale_value(name, params[name], group["necessary_flip"])
        return value >= group["necessary_min"]


    def get_personality_tier(self, group, score):
        winner = 0  # default is Normal
        for tier in group["tiers"]:
            if score >= tier["points"]:
                winner = tier["personality"]
        return winner


    def calculate_personality(self, params):
        group_scores = []

        for group_id, group_data in self.groups_data.items():
            if not self.meets_group_necessary_requirements(params, group_data):
                continue

            score = self.calculate_group_score(params, group_data)

            # using numeric index as a tiebreaker here
            key = (score, group_data["index"])
            group_scores.append((key, group_data))

        if not group_scores:
            # if no groups are eligible, we're Normal
            return 0

        # find the best group!
        (winner_score, _), winner_group = max(group_scores)
        return self.get_personality_tier(winner_group, winner_score)

    def calculate_personality_from_data(self, data):
        dump = self.open_dump(data)
        dump.unlock()
        if dump.data[0x1BC:0x1F6] != bytes.fromhex("00" * 0x3a):
            params = self.decode_behavior_params(dump)
            personality = self.calculate_personality(params)
            return personality_names[personality]
        else:
            return "Normal"

# binutils = NFCTools()
#
# with open('test.txt', 'rb') as test:
#     bin = binutils.txt_to_bin(test.read())
# with open('test2.bin', 'wb') as test:
#     test.write(bin)