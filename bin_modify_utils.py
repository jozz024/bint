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

# Got yelled at for having all of these classes inheret from binutils but idrc
# it makes the code cleaner imo

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
        # If the bin has a length of 540, pass it right into the amiibodump class
        if len(bin_dump) == 540:
            dump = AmiiboDump(self.keys, bin_dump)
            return dump
        # If the bin is larger/smaller than 540, resize it to be 540
        elif 532 <= len(bin_dump) <= 572:
            if len(bin_dump) < 540:
                # add a byte to the bin until it hits 540
                while len(bin_dump) < 540:
                    bin_dump += b'\x00'
                dump = AmiiboDump(self.keys, bin_dump)
                return dump
            if len(bin_dump) > 540:
                # shave the ending bytes off of the bin
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
        # set the amiibo nickname to the given name
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
        # open the json containing all of the transplantable characters
        character_json = open('assets/characters.json')
        characters = json.load(character_json)
        dump = self.open_dump(data)
        dump.unlock()
        for character in characters['characters']:
            # check if the given character nane is the same as the name
            if character_name.title() == character["name"]:
                dump.data[84:92] = bytes.fromhex(character["id"]) # mide said this didnt work for him, i think it was a skill issue
                # shuffles the serial number when you transplant
                dump.uid_hex = self.shuffle_sn()
                dump.lock()
                return dump.data
            # check translation table in case they didnt use the real name
            elif TRANSLATION_TABLE_CHARACTER_TRANSPLANT[character_name.lower().replace(' ', '')].title() == character["name"]:
                # refer to above for what this stuff is doing
                dump.data[84:92] = bytes.fromhex(character["id"])
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
        # check if they used a different wording for the skill's name
        if skill in SPIRITSKILLTABLE:
            # get the skill id from the skill name
            skill_id = SPIRITSKILLS[SPIRITSKILLTABLE[skill]]
            # return the skill id and the skill name
            return skill_id, SPIRITSKILLTABLE[skill]
        else:
            skill_id = SPIRITSKILLS[skill]
        return skill_id, skill
        # NOTE: We return skill id and skill name because of the translation

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
        # set the max attack + defense to be 5000
        maxstats = 5000
        # storing the amount of slots filled
        slotsfilled = (
            SKILLSLOTS[skill_1.lower()]
            + SKILLSLOTS[skill_2.lower()]
            + SKILLSLOTS[skill_3.lower()]
        )
        # if only one slot is filled, only subtract 300 from the maximum stat count
        if slotsfilled == 1:
            maxstats = maxstats - 300
        # if two slots are filled, subtract 500 from the maximum stat count
        if slotsfilled == 2:
            maxstats = maxstats - 500
        # if two slots are filled, subtract 500 from the maximum stat count
        if slotsfilled == 3:
            maxstats = maxstats - 800
        # return nothing if the stats are okay
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
        # get the skill ids and names from the name
        skill_1, skill_1_name = self.validate_skill(skill_1_name)
        skill_2, skill_2_name = self.validate_skill(skill_2_name)
        skill_3, skill_3_name = self.validate_skill(skill_3_name)

        dump = AmiiboDump(self.keys, data)
        dump.unlock()

        # validate the entire loadout, will error out if it isnt correct
        self.validate_loadout(attack, defense, skill_1_name, skill_2_name, skill_3_name)

        # set all of the skills and stats
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
        # start off with a fully 0'd out 540 byte block
        bin = bytes.fromhex('00' * 540)
        # initialize the dump, and set is_locked to false so it doesn't verify anything yet
        dump = AmiiboDump(self.keys, bin, False)
        dump.uid_hex = self.shuffle_sn()
        dump.amiibo_nickname = 'Ryujinx'
        # internal + static lock
        dump.data[0x09:0x0C] = bytes.fromhex('480FE0')
        # CC
        dump.data[0x0C:0x10] = bytes.fromhex('F110FFEE')
        # 0xA5 lol
        dump.data[0x10] = 0xA5
        # write counter
        dump.data[0x11:13] = bytes.fromhex(self.gen_random_bytes(2))
        # settings
        dump.data[0x14:0x16] = bytes.fromhex('3000')
        # crc counter
        dump.data[0x16:0x18] = bytes.fromhex(self.gen_random_bytes(2))
        # last write date
        dump.data[0x1A:0x1C] = bytes.fromhex(self.gen_random_bytes(2))
        # owner mii
        dump.data[0xA0:0x100] = bytes.fromhex('03 00 00 40 EB A5 21 1A E1 FD C7 59 D0 5A A5 4D 44 0D 56 BD 21 CA 00 00 00 00 4D 00 69 00 69 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 40 40 00 00 21 01 02 68 44 18 26 34 46 14 81 12 17 68 0D 00 00 29 00 52 48 50 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 14 6C'.replace(' ', ''))
        # application titleid
        dump.data[0x100:0x108] = bytes.fromhex('01006A803016E000')
        # 2nd write counter
        dump.data[0x108:0x10A] = bytes.fromhex(self.gen_random_bytes(2))
        # dynamic lock + rfui
        dump.data[0x208:0x20C] = bytes.fromhex('01000FBD')
        # cfg0 + cfg1
        dump.data[0x20c:0x214] = bytes.fromhex('000000045F000000')
        # 2 extra bytes get added somewhere, i cant figure out where so i just remove them for now
        dump.data = dump.data[:-2]
        return dump

    def bin_to_json(self, data):
        # initialize a dict to hold all of the data
        basejson = {}
        dump = self.open_dump(data)
        dump.unlock()
        # fileversion is always 0
        basejson['FileVersion'] = 0
        # amiibo name
        basejson['Name'] = dump.amiibo_nickname
        # uuid
        basejson['TagUuid'] = b64encode(dump.data[0x0:0x08]).decode('ASCII')
        # ID of the amiibo
        basejson['AmiiboId'] = dump.data[84:92].hex()
        # first write date
        basejson['FirstWriteDate'] = datetime.now().isoformat()
        # last write date
        basejson['LastWriteDate'] = datetime.now().isoformat()
        # write counter
        basejson['WriteCounter'] = dump.write_counter
        # applicationarea + app id
        basejson['ApplicationAreas'] = [
            {
                "ApplicationAreaId": int(dump.app_id.hex(), 16),
                "ApplicationArea": b64encode(dump.app_area).decode('ASCII'),
            }
        ]
        return json.dumps(basejson, indent=4)

    def json_to_bin(self, ryujinx_json):
        # loads the given json data
        ryujinx_json = json.loads(ryujinx_json)
        # generate a bin
        dump = self.generate_bin()
        # write the name to the bin if it exists
        if 'Name' in ryujinx_json:
            dump.amiibo_nickname = ryujinx_json['Name']
        # write the character to the bin
        dump.data[84:92] = bytes.fromhex(ryujinx_json['AmiiboId'])
        # write counter
        dump.write_counter = ryujinx_json['WriteCounter']
        # write apparea stuff
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
            # not the fix, but produces more accurate results
            return 0.25

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
        # check if training data is not null
        if dump.data[0x1BC:0x1F6] != bytes.fromhex("00" * 0x3a):
            params = self.decode_behavior_params(dump)
            personality = self.calculate_personality(params)
            return personality_names[personality]
        # if it is, return normal
        else:
            return "Normal"
