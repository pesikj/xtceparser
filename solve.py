#!/usr/bin/env python3
# -*- coding: utf-8 -*
# /////////////////////////////////////////////////////////////////////////////
#   ____                   ____          _
# |  _ \  ___  ___ _ __  / ___|___   __| | ___
# | | | |/ _ \/ _ \ '_ \| |   / _ \ / _` |/ _ \
# | |_| |  __/  __/ |_) | |__| (_) | (_| |  __/
# |____/ \___|\___| .__/ \____\___/ \__,_|\___|
#                 |_|
#
# Author: Jon Rasiko, DeepCode.ca
# Version: 1.0
# Date:
#
# License
# --------
# This file is subject to the terms and conditions defined in
# file 'LICENSE.txt', which is part of this source code package.
#
# Description:
# -------------
# This Python script reads a XML Telemetry & Command Exchange (XTCE) 
# definition file and attempts to decode a given data blob.
#
# This script was generated for the Hack-a-Sat Quals 2020 for the "Can you year me now?"
# challenge. 
#
# References:
# -------------
# https://ntrs.nasa.gov/archive/nasa/casi.ntrs.nasa.gov/20090017706.pdf
# /////////////////////////////////////////////////////////////////////////////

import os
import sys
import socket
import argparse
import bitstring
import logging

import xml.etree.ElementTree as ET

OPT_VERBOSE_HELP = "Display additional information about execution."

logger = logging.getLogger(__name__)

def main(argv):
    parser = argparse.ArgumentParser(
        prog=argv[0],
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Simple XML Telemetry & Command Exchange (XTCE) Parser in Python3",
        epilog="")
    parser.add_argument('-v', '--verbose',
                        default=False,
                        action="store_true",
                        dest="is_debug",
                        help=OPT_VERBOSE_HELP)

    # Parse command-line arguents
    args = parser.parse_args(args=argv[1:])


    # Set application properties based on the environment
    # if args.is_debug:
    if args.is_debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)


    print("")

    # 6900 a5d6 0b00 a113 9f5c faf7 4612 7aea

    #0000450 0000 e367 000c 0306 0007 00f9 7caf 6900
    #0000460 b3d6 0b00 5f1b faff eea5 d51c 33d1 9a46
    #0000470 6700 0de3 0600 1603 f900 af00 007c d669
    #0000480 00b4 240b db03 3df1 9b8f a80e 55b2 003e
    #0000490 e466 00d3 cd57 0eb3 7b7f f6b7 b7cb 5e16
    #00004a0 594c 6833 76d7 d9fe e276 c9cb d0d7 0000
    #00004b0 0000 0000 0000 0000 0000 0000 0000 0000

    #0000740 0000 0000 0000 0000 0000 0000 d669 00bc
    #0000750 be0b 1b0c d320 71e2 3742 c61d 0006 e367
    #0000760 0016 0306 0086 00c9 3caf 6900 bdd6 0b00
    #0000770 8dd3 a40c 0218 c8fd a6e8 ecea 6700 17e3
    #0000780 0600 7f03 c000 af00 003c e466 00d8 cd57
    #0000790 0eb3 7b7f f6b7 b7cb 5e16 594c 6833 76d7
    #00007a0 d9fe e276 c9cb d0d7 0000 0000 0000 0000
    #00007b0 0000 0000 0000 0000 0000 0000 0000 0000
    b =  bitstring.BitStream("0x6900a5d60b00a1139f5cfaf746127aea")
    # will work:
    #b =  bitstring.BitStream("0x0069d6a5000b13a1...")


    file_xtce = "telemetry-min.xtce"
    tree = ET.parse(file_xtce)

    # 6.1 The Root Object – The SpaceSystem
    root = tree.getroot()
    ss_ns = "http://www.omg.org/space/xtce"
    ss_name = root.get("name")

    ss_desc = root.find("{http://www.omg.org/space/xtce}LongDescription").text
    logger.info(f"SpaceSystem: {ss_name}")
    logger.info( "----------------------")
    logger.info(ss_desc)
    ss_header = root.find("{http://www.omg.org/space/xtce}Header")
    ss_tlm = root.find("{http://www.omg.org/space/xtce}TelemetryMetaData")
    ss_parameter_type_set = ss_tlm.find("{http://www.omg.org/space/xtce}ParameterTypeSet")
    ss_parameter_set = ss_tlm.find("{http://www.omg.org/space/xtce}ParameterSet")
    ss_container_set = ss_tlm.find("{http://www.omg.org/space/xtce}ContainerSet")
    ss_containers = ss_container_set.findall("{http://www.omg.org/space/xtce}SequenceContainer")

    if ss_parameter_set is None:
        logger.error(f"No 'ParameterSet' found in file '{file_xtce}.")
        sys.exit(1)

    for ss_container in ss_containers:
        is_abstract = ss_container.get("abstract") == "true"
        logger.debug(f"{ss_container}: abstract={is_abstract}")
        for parameter in ss_container.find("{http://www.omg.org/space/xtce}EntryList").findall("{http://www.omg.org/space/xtce}ParameterRefEntry"):
            param_ref = parameter.get("parameterRef")
            ss_param = ss_parameter_set.find("./{http://www.omg.org/space/xtce}Parameter[@name='" + param_ref + "']")
            param_type_ref = ss_param.get("parameterTypeRef")
            ss_type = ss_parameter_type_set.find("./*[@name='" + param_type_ref + "']")
            if ss_type.tag == "{http://www.omg.org/space/xtce}IntegerParameterType":
                size_in_bits = int(ss_type.find("{http://www.omg.org/space/xtce}IntegerDataEncoding").get("sizeInBits"))
                signed = ss_type.get("signed").lower() == "signed"
                logger.debug(f"{param_ref}: {size_in_bits} bit(s), signed={signed} ,{ss_type.tag}")

                if signed:
                    t = f"int:{size_in_bits}"
                else:
                    t = f"uint:{size_in_bits}"
                v = b.read(t)
                logger.info(f"{param_ref}: {hex(v)} {chr(v)}")
            elif ss_type.tag == "{http://www.omg.org/space/xtce}FloatParameterType":
                v_unit = ""
                size_in_bits = int(ss_type.get("sizeInBits"))
                ss_unit = ss_type.find("{http://www.omg.org/space/xtce}UnitSet")
                if ss_unit is not None:
                    ss_type_unit = ss_unit.find("{http://www.omg.org/space/xtce}Unit")
                    if ss_type_unit is not None:
                        v_unit = ss_type_unit.get("description")
                
                v = b.read(f"float:{size_in_bits}")
                ss_int_encoding = ss_type.find("{http://www.omg.org/space/xtce}IntegerDataEncoding")

                logger.info(f"{param_ref}: {size_in_bits} bit(s), signed={signed}, unit='{v_unit}' ,{ss_type.tag}")
            elif ss_type.tag == "{http://www.omg.org/space/xtce}EnumeratedParameterType":
                size_in_bits = int(ss_type.find("{http://www.omg.org/space/xtce}IntegerDataEncoding").get("sizeInBits"))
                v = b.read(size_in_bits)
                for ss_enum in ss_type.find("{http://www.omg.org/space/xtce}EnumerationList").findall("{http://www.omg.org/space/xtce}Enumeration"):
                    enum_label = ss_enum.get("label")
                    enum_value = ss_enum.get("value")
                    logger.info(f"{param_ref}: {size_in_bits} bit(s), label={enum_label}, value={enum_value}, {ss_type.tag}")
                    logger.info(f"{param_ref}: {hex(v)} {chr(v)}")
            else:
                logger.warning(f"Unknown data type: {ss_type.tag}")
             

    return 0


def entry_point():
    """Zero-argument entry point for use with setuptools/distribute."""
    raise SystemExit(main(sys.argv))


if __name__ == '__main__':
    sys.exit(entry_point())