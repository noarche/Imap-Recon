#!/usr/local/opt/python@3.8/bin/python3
# -*- coding: utf-8 -*-

__author__ = 'D'
__date__ = 'D'
__version__ = 'D'
__contact__ = 'D'

'''
---------------------------------
Functions for Handling Combolists
---------------------------------
'''

# [IMPORTS]
# ---------
import sys
from datetime import datetime
from inc_etc import result
from inc_etc import email_verification
from inc_etc import blacklist_check
from concurrent.futures import ThreadPoolExecutor

# [FUNCTIONS]
# -----------

def process_combo(line, loaded_combos, output_blacklist, output_clean):
    try:
        # replace any other separator than semicolon in combos:
        new_combo = line.replace(';', ':').replace(',', ':').replace('|', ':')
        # check combo for email address:
        with_email = email_verification(new_combo.split(':')[0])
        if not with_email:
            return
        # check email domain against provider blacklist:
        if blacklist_check(new_combo.split(':')[0]):
            result(output_blacklist, new_combo.rstrip('\n'))
            return
        # add unique combos to target-list:
        if new_combo.rstrip('\n') in loaded_combos:
            return
        else:
            loaded_combos.add(new_combo.rstrip('\n'))
            result(output_clean, new_combo.rstrip('\n'))
    except Exception as e:
        pass

def comboloader(input_file):
    '''
    Loads combos from a given file using 100 threads.

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

    try:
        with open(input_file, 'r') as file:
            with ThreadPoolExecutor(max_workers=100) as executor:
                # Submit each line to the thread pool
                futures = [executor.submit(process_combo, line, loaded_combos, output_blacklist, output_clean) for line in file]

                # Ensure all threads are completed
                for future in futures:
                    future.result()

        # write logs when finished and quit:
        result(output_blacklist, f'\nCombos imported from file: {input_file}.\n=== END OF IMPORT ===')
        result(output_clean, f'\nCombos imported from file: {input_file}.\n=== END OF IMPORT ===')
    except Exception as e:
        result(output_blacklist, f'\nAn error occurred while importing the combos from file: {input_file}.\n=== END OF IMPORT ===')
        result(output_clean, f'\nAn error occurred while importing the combos from file: {input_file}.\n=== END OF IMPORT ===')

    return loaded_combos
