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
__version__ = 'D'
__contact__ = 'D'

'''
----------------------------------------------------------
Functions for Sending Test Messages with found SMTP Logins
----------------------------------------------------------
'''

# [IMPORTS]
# ---------

import sys
import json
import uuid
import smtplib
import ssl
from random import randint
from email.message import EmailMessage

# [FUNCTIONS]
# -----------

def mailer(default_email, target_email, target_host, target_port, target_user, target_password):
    '''
    Tests found SMTP logins by sending a message to the user's email.

    :param str default_email: user email for receiving test messages
    :param str target_email: email of found smtp login
    :param str target_host: host of found smtp login
    :param int target_port: port of smtp host
    :param str target_user: user-id of found smtp login
    :param str target_password: password for user-id
    :return: True (email sent), False (no email sent)
    '''
    try:
        # set variables and stuff:
        sslcontext = ssl.create_default_context()
        try:
            sslcontext.check_hostname = False
            sslcontext.verify_mode = ssl.CERT_NONE
        except:
            pass
        content_loaded = False
        try:
            with open('inc_emailcontent.json') as included_imports:
                json_object = json.load(included_imports)
                email_titles = (json_object['email_titles'])
                email_firstlines = (json_object['email_firstlines'])
                email_secondlines = (json_object['email_secondlines'])
                email_thirdlines = (json_object['email_thirdlines'])
            content_loaded = True
        except:
            email_titles = []
            email_firstlines = []
            email_secondlines = []
            email_thirdlines = []
        # generate random id:
        random_id = str(uuid.uuid4().hex)[0:6].upper()
        # generate parts of the message using the libraries:
        if content_loaded == True:
            letter_subject = str(
                email_titles[randint(0, len(email_titles) - 1)] + random_id
            )
            letter_firstline = str(
                email_firstlines[randint(0, len(email_firstlines) - 1)]
            )
            letter_secondline= str(
                email_secondlines[randint(0, len(email_secondlines) - 1)]
            )
            letter_thirdline = str(
                email_thirdlines[randint(0, len(email_thirdlines) - 1)]
            )
        # if previous step fails, this fallback is used:
        else:
            letter_subject = str(
                f'Test Message ID{random_id}'
            )
            letter_firstline = str(
                'thank you for using imap-recon.'
            )
            letter_secondline = str(
                'the following smtp account was found.'
            )
            letter_thirdline = str(
                'this hit has been saved to the results dir, too.'
            )
        # generate the testmessage:
        message = str(
            letter_firstline + '\n'
            + letter_secondline + '\n'
            + f'email: {target_email}\n'
            + f'smtp host: {target_host}:{str(target_port)}\n'
            + f'user-id: {target_user}\n'
            + f'password: {target_password}\n'
            + letter_thirdline + '\n'
        )
        # pack the testmessage:
        letter = EmailMessage()
        letter.set_content(message)
        letter['Subject'] = str(f'{letter_subject}')
        letter['From'] = str(f'{target_email}')
        letter['To'] = str(f'{default_email}')
        # connect to smtp server:
        if target_port == 465:
            mailer = smtplib.SMTP_SSL(
                host=target_host,
                port=target_port,
                timeout=float(60),
                context=sslcontext
            )
            mailer.ehlo()
        else:
            mailer = smtplib.SMTP(
                host=target_host,
                port=target_port,
                timeout=float(60)
            )
            mailer.ehlo()
            try:
                mailer.starttls(
                    context=sslcontext
                )
                mailer.ehlo()
            except:
                pass
        mailer.login(
            user=target_user,
            password=target_password
        )
        # send email and quit:
        mailer.send_message(letter)
        mailer.quit()
        return True
    except:
        return False




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