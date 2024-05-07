#!/usr/local/opt/python@3.8/bin/python3
# -*- coding: utf-8 -*-

__author__ = 'DrPython3'
__date__ = '2021-12-04'
__version__ = '2.4'
__contact__ = 'https://github.com/DrPython3'

'''
---------------------------------
Functions for Handling Combolists
---------------------------------

Part of << Mail.Rip V3: https://github.com/DrPython3/MailRipV3 >>
'''

# [IMPORTS]
# ---------
import sys
from datetime import datetime
from inc_etc import result
from inc_etc import email_verification
from inc_etc import blacklist_check

# [FUNCTIONS]
# -----------

def comboloader(input_file):
    '''
    Loads combos from a given file.

    :param str input_file: file containing the combos
    :return: list with loaded combos
    '''
    # set variables:
    loaded_combos = set()
    output_blacklist = 'combos_blacklisted'
    output_clean = 'combos_loaded'
    # log message on start:
    timestamp = datetime.now()
    output_startup = (
        f'Comboloader started on: {timestamp.strftime("%Y-%m-%d %H:%M:%S")}, combofile: {input_file}\n'
        + '=' * 50
    )
    # logging import of combofile:
    result(output_blacklist, output_startup)
    result(output_clean, output_startup)
    # import the combos:
    try:
        with open(input_file, 'r') as file:
            for line in file:
                try:
                    # replace any other separator than semicolon in combos:
                    new_combo = line.replace(';', ':').replace(',', ':').replace('|', ':')
                    # check combo for email address:
                    with_email = email_verification(new_combo.split(':')[0])
                    if not with_email:
                        continue
                    # check email domain against provider blacklist:
                    if blacklist_check(new_combo.split(':')[0]):
                        result(output_blacklist, new_combo.rstrip('\n'))
                        continue
                    # add unique combos to target-list:
                    if new_combo.rstrip('\n') in loaded_combos:
                        continue
                    else:
                        loaded_combos.add(new_combo.rstrip('\n'))
                        result(output_clean, new_combo.rstrip('\n'))
                except Exception as e:
                    continue
        # write logs when finished and quit:
        result(output_blacklist, f'\nCombos imported from file: {input_file}.\n=== END OF IMPORT ===')
        result(output_clean, f'\nCombos imported from file: {input_file}.\n=== END OF IMPORT ===')
    except Exception as e:
        result(output_blacklist, f'\nAn error occurred while importing the combos from file: {input_file}.\n=== END OF IMPORT ===')
        result(output_clean, f'\nAn error occurred while importing the combos from file: {input_file}.\n=== END OF IMPORT ===')
    return loaded_combos

# DrPython3 (C) 2021 @ GitHub.com
