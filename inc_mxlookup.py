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

__author__ = 'D'
__date__ = 'D'
__version__ = '1.1'
__contact__ = 'D'

'''
--------------------------------------------
Functions for Reading MX Records of a Domain
--------------------------------------------
'''

# [IMPORTS]
# ---------

import sys
import socket
import dns.resolver
from inc_etc import domain_verification

# [FUNCTIONS]
# -----------

def get_host(default_timeout, email):
    '''
    Checks the DNS records of an email-domain for MX infos and returns any found SMTP URI.

    :param float default_timeout: connection timeout
    :param str email: email with domain to check
    :return: found (True, False), smtp_host (SMTP URI)
    '''
    # set variables and stuff:
    socket.setdefaulttimeout(default_timeout)
    found = False
    smtp_host = str('none')
    smtp_domain = str(email.split('@')[1])
    get_records = dns.resolver.Resolver(configure=False)
    # using OpenDNS DNS, replace on purpose:
    get_records.nameservers = ['208.67.222.222']
    records = get_records.resolve(smtp_domain, 'MX')
    counter = 0
    # extract host from records:
    while found == False:
        try:
            possible_host = str(records[counter]).split(' ')[1].rstrip('.')
            verify_domain = domain_verification(possible_host)
            if verify_domain == True:
                smtp_host = possible_host
                found = True
            else:
                counter += 1
        except:
            break
    return found, smtp_host




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