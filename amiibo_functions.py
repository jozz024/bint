from amiibo import AmiiboMasterKey
from ssbu_amiibo import SsbuAmiiboDump as AmiiboDump
import random
from dictionaries import *


class BinManager:
    def __init__(self, char_dict, key_directory="Brain_Transplant_Assets"):
        """
        This class manages bin files, does transplants and serial editing
        :param char_dict:
        """
        self.characters = char_dict
        self.key_directory = key_directory
        with open(
            r"/".join([self.key_directory, "unfixed-info.bin"]), "rb"
        ) as fp_d, open(
            r"/".join([self.key_directory, "locked-secret.bin"]), "rb"
        ) as fp_t:
            self.master_keys = AmiiboMasterKey.from_separate_bin(
                fp_d.read(), fp_t.read()
            )

    def __open_bin(self, bin_location=None, dump=None):
        """
        Opens a bin and makes it 540 bytes if it wasn't

        :param bin_location: file location of bin you want to open
        :return: opened bin
        """
        if dump == None: 
            bin_fp = open(bin_location, "rb")
        else:
            bin_fp = dump

        bin_dump = bytes()
        if dump == None: 
          for line in bin_fp:
            bin_dump += line
          bin_fp.close()
        else:
            bin_dump = bin_fp

        if len(bin_dump) == 540:
          if dump == None: 
            with open(bin_location, "rb") as fp:
                dump = AmiiboDump(self.master_keys, fp.read())
                return dump
          else:
            dump = AmiiboDump(self.master_keys, dump)
            return dump
        elif 532 <= len(bin_dump) <= 572:
            while len(bin_dump) < 540:
                bin_dump += b"\x00"
            if len(bin_dump) > 540:
                bin_dump = bin_dump[: -(len(bin_dump) - 540)]
            if dump == None: 
              b = open(bin_location, "wb")
              b.write(bin_dump)
              b.close()
            if dump == None: 
              with open(bin_location, "rb") as fp:
                dump = AmiiboDump(self.master_keys, fp.read())
            else:
                dump = AmiiboDump(self.master_keys, bin_dump)
            return dump
        else:
            return None


    def getBit(self, number, bit_index):
        return (number >> bit_index) % 2


    def getBits(self, number, bit_index, number_of_bits):
      # clears bits we don't care about
      inv_number = 255 - (number & ~(2**number_of_bits-1 << bit_index))

      return (number & inv_number) >> bit_index


    def setBit(self, number, bit_index, value):
      bit_index = 7 - bit_index
      # clears bit
      number = number & ~(1 << bit_index)
      # sets bit
      return number | (value << bit_index)


    def setBits(self, number, bit_index, number_of_bits, value):
      """
      Ex. setBits(b'11011100', 4, 3, b'0000') = 10001100
      :param number: input that you want to set bits in
      :param bit_index: range from 0 to 7, where 0 is the right most bit
      :param number_of_bits: range from 1 to 8
      :param value: value that you want the bits to be set to
      :return:
      """
      # clears bit
      number = number & ~(2**number_of_bits-1 << bit_index)
      # sets bit
      return number | (value << bit_index)


    def concatonateBits(self, left, right, right_size):
      # can't use right.bit_length() because of cases where right is 0 but is 2 bits
      left = left << right_size
      return left | right



    SECTIONS = {
    "Near": 7,
    "Offensive": 7,
    "Grounded": 7,
    "Attack Out Cliff": 6,
    "Dash": 7,
    "Return To Cliff": 6,
    "Air Offensive": 6,
    "Cliffer": 6,
    "Feint Master": 7,
    "Feint Counter": 7,
    "Feint Shooter": 7,
    "Catcher": 7,
    "100 Attacker": 6,
    "100 Keeper": 6,
    "Attack Cancel": 6,
    "Smash Holder": 7,
    "Dash Attacker": 7,
    "Critical Hitter": 6,
    "Meteor Smasher": 6,
    "Shield Master": 7,
    "Just Shield Master": 6,
    "Shield Catch Master": 6,
    "Item Collector": 5,
    "Item Throw to Target": 5,
    "Dragoon Collector": 4,
    "Smash Ball Collector": 4,
    "Hammer Collector": 4,
    "Special Flagger": 4,
    "Item Swinger": 5,
    "Homerun Batter": 4,
    "Club Swinger": 4,
    "Death Swinger": 4,
    "Item Shooter": 5,
    "Carrier Breaker": 5,
    "Charger": 5,
    "Appeal": 5,
    "Advantageous Fighter": 14,
    "Weaken Fighter": 14,
    "Revenge": 14,
    "Stage Enemy": 14,
    "Forward Tilt": 10,
    "Up Tilt": 10,
    "Down Tilt": 10,
    "Forward Smash": 10,
    "Up Smash": 10,
    "Down Smash": 10,
    "Neutral Special": 10,
    "Side Special": 10,
    "Up Special": 10,
    "Down Special": 10,
    "Forward Air": 9,
    "Back Air": 9,
    "Up Air": 9,
    "Down Air": 9,
    "Neutral Special Air": 9,
    "Side Special Air": 9,
    "Up Special Air": 9,
    "Down Special Air": 9,
    "Front Air Dodge": 8,
    "Back Air Dodge": 8,
    "APPEAL_HI": 7,
    "APPEAL_LW": 7,
    }


    def bineval(self, bin_location):
      
      dump = self.__open_bin(dump=bin_location)
      dump.unlock()
      bits_left = 8
      current_index = 444
      output = ""
      for sectione in self.SECTIONS:
        section = self.SECTIONS[sectione]
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

        output += f"{sectione}: {value/(2**section-1)*100}\n"
      return f"```{output}```"


    def update_char_dictionary(self, new_char_dict):
        """
        Updates character dictionary

        :param new_char_dict: dictionary to replace old one with
        :return: None
        """
        self.characters = new_char_dict

    def randomize_sn(self, dump=None, dump_ = None):
        """
        Randomizes the serial number of a given bin dump
        :param dump: Pyamiibo dump of a bin
        :return: None
        """
        if dump_ != None:
            dump = self.__open_bin(dump = dump_)
        serial_number = "04"
        while len(serial_number) < 20:
            temp_sn = hex(random.randint(0, 255))
            # removes 0x prefix
            temp_sn = temp_sn[2:]
            # creates leading zero
            if len(temp_sn) == 1:
                temp_sn = "0" + temp_sn
            serial_number += " " + temp_sn
        # if unlocked, keep it unlocked, otherwise unlock and lock
        if not dump.is_locked:
            dump.uid_hex = serial_number
        else:
            dump.unlock()
            dump.uid_hex = serial_number
            dump.lock()
        return dump

    def setspirits(
        self,
        attack,
        defense,
        ability1,
        ability2,
        ability3,
        dump
    ):
        try:
            ability1 = SPIRITSKILLTABLE[ability1.lower()]
        except KeyError:
            pass
        try:
            ability2 = SPIRITSKILLTABLE[ability2.lower()]
        except KeyError:
            pass
        try:
            ability3 = SPIRITSKILLTABLE[ability3.lower()]
        except KeyError:
            pass
        hexatk = int(attack)
        hexdef = int(defense)
        hexability1 = int(SPIRITSKILLS[ability1.lower()])
        hexability2 = int(SPIRITSKILLS[ability2.lower()])
        hexability3 = int(SPIRITSKILLS[ability3.lower()])
        maxstats = 5000

        dump = self.__open_bin(dump=dump)
        dump.unlock()

        slotsfilled = (
            SKILLSLOTS[ability1.lower()]
            + SKILLSLOTS[ability2.lower()]
            + SKILLSLOTS[ability3.lower()]
        )
        if slotsfilled == 1:
            maxstats = maxstats - 300
        if slotsfilled == 2:
            maxstats = maxstats - 500
        if slotsfilled == 3:
            maxstats = maxstats - 800
        if hexatk + hexdef <= maxstats:
            dump.data[0x1A4:0x1A6] = hexatk.to_bytes(2, "little")
            dump.data[0x1A6:0x1A8] = hexdef.to_bytes(2, "little")
            dump.data[0x140:0x141] = hexability1.to_bytes(1, "little")
            dump.data[0x141:0x142] = hexability2.to_bytes(1, "little")
            dump.data[0x142:0x143] = hexability3.to_bytes(1, "little")
            dump.lock()
            return dump.data
        else:
            dump.lock()
            raise IndexError("Illegal Bin")

    def dump_to_amiitools(self, dump):
        """Convert a standard Amiibo/NTAG215 dump to the 3DS/amiitools internal
        format.
        """
        internal = bytearray(dump)
        internal[0x000:0x008] = dump[0x008:0x010]
        internal[0x008:0x028] = dump[0x080:0x0A0]
        internal[0x028:0x04C] = dump[0x010:0x034]
        internal[0x04C:0x1B4] = dump[0x0A0:0x208]
        internal[0x1B4:0x1D4] = dump[0x034:0x054]
        internal[0x1D4:0x1DC] = dump[0x000:0x008]
        internal[0x1DC:0x208] = dump[0x054:0x080]
        return internal

    def decrypt(self, dump):
        dump = AmiiboDump(self.master_keys, dump)
        dump.unlock()
        data = self.dump_to_amiitools(dump.data)
        return data

    def personalityedit(
        self,
        bin_location,
        aggression,
        edgeguard,
        anticipation,
        defensiveness,
        saveAs_location,
    ):
        aggression = int(aggression)
        edgeguard = int(edgeguard)
        anticipation = int(anticipation)
        defensiveness = int(defensiveness)
        with open(bin_location, "rb") as fp:
            dump = AmiiboDump(self.master_keys, fp.read())
        dump.unlock()
        dump.data[0x1BC:0x1BE] = aggression.to_bytes(2, "little")
        dump.data[0x1BE:0x1C0] = edgeguard.to_bytes(2, "little")
        dump.data[0x1C0:0x1C2] = anticipation.to_bytes(2, "little")
        dump.data[0x1C2:0x1C4] = defensiveness.to_bytes(2, "little")
        dump.lock()
        with open(saveAs_location, "wb") as fp:
            fp.write(dump.data)

    def transplant(self,  character, saveAs_location = None, randomize_SN=False, bin_location = None, dump = None):
        """
        Takes a bin and replaces it's character ID with given character's ID

        :param bin_location: file location of bin to use
        :param character: Character from char_dict you want to transplant into
        :param randomize_SN: If the bin SN should be randomized or not
        :param saveAs_location: location to save new bin
        :return: Character it was transplanted into
        """
        if dump is None:
            dump = self.__open_bin(bin_location)
            using_stream = False
        else: 
            dump = self.__open_bin(dump=dump)
            using_stream = True
        mii_transplant = "B3E038270F1D4C92ABCEF5427D67F9DCEC30CE3000000000000000000000000000000000000000000040400000000000001F02000208040304020C1302040306020C010409171304030D080000040A0008040A0004021400"
        if dump is None:
            return None

        if randomize_SN:
            self.randomize_sn(dump)
        hex_tag = self.characters[character]
        hex_tag = (
            hex_tag[0]
            + hex_tag[1]
            + " "
            + hex_tag[2]
            + hex_tag[3]
            + " "
            + hex_tag[4]
            + hex_tag[5]
            + " "
            + hex_tag[6]
            + hex_tag[7]
            + " "
            + hex_tag[8]
            + hex_tag[9]
            + " "
            + hex_tag[10]
            + hex_tag[11]
            + " "
            + hex_tag[12]
            + hex_tag[13]
            + " "
            + hex_tag[14]
            + hex_tag[15]
        )

        dump.unlock()
        dump.data[0x148:0x1A0] = bytes.fromhex(mii_transplant)
        dump.data[84:92] = bytes.fromhex(hex_tag)
        dump.lock()
        if using_stream == False:
            with open(saveAs_location, "wb") as fp:
                fp.write(dump.data)
            return character
        else:
            return dump.data

    def serial_swapper(self, donor, receiver, saveAs_location):
        """
        Transfer the SN of the donor to the receiver, saves new bin at given location

        :param donor: bin to give SN
        :param receiver: bin to receive SN
        :param saveAs_location: location to save new bin
        :return: None
        """
        donor_dump = self.__open_bin(donor)
        receiver_dump = self.__open_bin(receiver)

        if donor_dump is None or receiver_dump is None:
            return None

        receiver_dump.unlock()
        # RO areas from https://wiki.gbatemp.net/wiki/Amiibo give FP metadata needed for transplant
        receiver_dump.data[0:17] = donor_dump.data[0:17]
        receiver_dump.data[52:129] = donor_dump.data[52:129]
        receiver_dump.data[520:533] = donor_dump.data[520:533]
        receiver_dump.lock()

        with open(saveAs_location, "wb") as fp:
            fp.write(receiver_dump.data)

        return True
