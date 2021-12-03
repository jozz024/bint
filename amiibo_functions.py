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

    def __open_bin(self, bin_location):
        """
        Opens a bin and makes it 540 bytes if it wasn't

        :param bin_location: file location of bin you want to open
        :return: opened bin
        """
        bin_fp = open(bin_location, "rb")

        bin_dump = bytes()
        for line in bin_fp:
            bin_dump += line
        bin_fp.close()

        if len(bin_dump) == 540:
            with open(bin_location, "rb") as fp:
                dump = AmiiboDump(self.master_keys, fp.read())
                return dump
        elif 532 <= len(bin_dump) <= 572:
            while len(bin_dump) < 540:
                bin_dump += b"\x00"
            if len(bin_dump) > 540:
                bin_dump = bin_dump[: -(len(bin_dump) - 540)]
            b = open(bin_location, "wb")
            b.write(bin_dump)
            b.close()

            with open(bin_location, "rb") as fp:
                dump = AmiiboDump(self.master_keys, fp.read())
                return dump
        else:
            return None

    def update_char_dictionary(self, new_char_dict):
        """
        Updates character dictionary

        :param new_char_dict: dictionary to replace old one with
        :return: None
        """
        self.characters = new_char_dict

    def randomize_sn(self, dump=None, bin_location=None):
        """
        Randomizes the serial number of a given bin dump
        :param dump: Pyamiibo dump of a bin
        :return: None
        """
        if bin_location is not None:
            dump = self.__open_bin(bin_location)
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
        if bin_location is not None:
            with open(bin_location, "wb") as fp:
                fp.write(dump.data)

    def setspirits(
        self,
        bin_location,
        attack,
        defense,
        ability1,
        ability2,
        ability3,
        saveAs_location,
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

        dump = self.__open_bin(bin_location)
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
        print(hexatk + hexdef)
        print(maxstats)
        if hexatk + hexdef <= maxstats:
            dump.data[0x1A4:0x1A6] = hexatk.to_bytes(2, "little")
            dump.data[0x1A6:0x1A8] = hexdef.to_bytes(2, "little")
            dump.data[0x140:0x141] = hexability1.to_bytes(1, "little")
            dump.data[0x141:0x142] = hexability2.to_bytes(1, "little")
            dump.data[0x142:0x143] = hexability3.to_bytes(1, "little")
            dump.lock()
            with open(saveAs_location, "wb") as fp:
                fp.write(dump.data)
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

    def decrypt(self, bin_location, saveAs_location):
        with open(bin_location, "rb") as fp:
            dump = AmiiboDump(self.master_keys, fp.read())
        dump.unlock()
        data = self.dump_to_amiitools(dump.data)
        with open(saveAs_location, "wb") as fp:
            fp.write(data)

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

    def transplant(self, bin_location, character, saveAs_location, randomize_SN=False):
        """
        Takes a bin and replaces it's character ID with given character's ID

        :param bin_location: file location of bin to use
        :param character: Character from char_dict you want to transplant into
        :param randomize_SN: If the bin SN should be randomized or not
        :param saveAs_location: location to save new bin
        :return: Character it was transplanted into
        """

        dump = self.__open_bin(bin_location)
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
        with open(saveAs_location, "wb") as fp:
            fp.write(dump.data)
        return character

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
