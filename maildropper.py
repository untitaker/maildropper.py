import sys
import os
import email
import email.parser
import email.generator

import datetime
import time
import imaplib
from io import BytesIO

pjoin = os.path.join

def _parse_message():
    return email.parser.BytesParser().parse(sys.stdin.buffer)

def _get_logentry(msg, date):
    return ('\nDate (datetime.now): {dt_now}'
            '\nDate (header): {msg["Date"]}'
            '\nFrom: {msg["From"]}'
            '\nTo: {msg["To"]}'
            '\nSubject: {msg["Subject"]}'
            '\nErrors: {msg.defects}').format(dt_now=date, msg=msg)

def _imap_rv(x):
    assert x[0] == 'OK', x
    return x[1]


class DeliveredMessage(Exception):
    pass


class Maildropper(object):
    def log(self, msg):
        msg = str(msg)
        if '\n' in msg:
            for sub in msg.split('\n'):
                self.log(sub)
        elif '\r' in msg:
            for sub in msg.split('\r'):
                self.log(sub)
        else:
            self.logfile.write('\n[' + self.msg_id + ']  ' + msg)

    def header(self, name):
        return str(self.msg.get(name, ''))

    def __init__(self, user, pwd, host, port=993, ssl=True):
        self.user = user
        self.pwd = pwd
        self.host = host
        self.port = port
        self.ssl = ssl
        self.logfile = sys.stdout
        self._init_imap()
        self._init_msg()
        self._ctx_manager = False

    def __enter__(self):
        self._ctx_manager = True
        return self

    def __exit__(self, cls, val, tb):
        self._ctx_manager = False
        if cls is DeliveredMessage:
            return True
        elif cls is None:
            raise RuntimeError('Didn\'t deliver message.')

    def _init_msg(self):
        self.msg = _parse_message()
        self.now = now = datetime.datetime.now()
        self.msg_id = self.msg['X-Maildrop-Id'] = str(hash(now))
        self.log(_get_logentry(self.msg, now))

    def _init_imap(self):
        c = self.ssl and imaplib.IMAP4_SSL or imaplib.IMAP4
        self.imap = c(self.host, self.port)
        _imap_rv(self.imap.login(self.user, self.pwd))

    @staticmethod
    def _process_flags(flags):
        allowed_flags = ('flagged', 'seen', 'answered', 'draft')

        def inner():
            for flag, value in flags.items():
                if flag not in allowed_flags:
                    raise RuntimeError('Flag not allowed: {}'.format(flag))
                if value:
                    yield '\\' + flag.title()
        return ' '.join(sorted(inner()))

    def drop(self, folder, **flags):
        if not self._ctx_manager:
            raise RuntimeError('Need to be in context manager.')
        try:
            f = BytesIO()
            gen = email.generator.BytesGenerator(f)
            gen.flatten(self.msg)
            self.log('Writing to {}'.format(folder))
            _imap_rv(self.imap.select(folder))
            _imap_rv(self.imap.append(
                folder,
                self._process_flags(flags),
                imaplib.Time2Internaldate(time.time()),
                f.getvalue()
            ))
            self.imap.close()
            self.imap.logout()
        except Exception:
            pass
        else:
            raise DeliveredMessage()

    def has_parent_in(self, folder):
        '''Check if the message this one is a reply to
        is in $folder'''
        in_reply = self.header('In-Reply-To')
        if not in_reply:
            return False
        in_reply = in_reply.split('>')[0] + '>'
        if '"' in in_reply:
            self.log('QUOTE IN IN-REPLY HEADER')
            return False
        _imap_rv(self.imap.select(folder))
        res = _imap_rv(self.imap.search(
            None,
            'HEADER Message-ID "{}"'.format(in_reply)
        ))
        return bool(res[0].strip())
