import sys
import os
import email
import email.parser
import email.generator
import datetime

pjoin = os.path.join


class Maildropper(object):
    logfile = None
    msg = None
    msg_id = None
    dry_run = None

    def __init__(self, logfile=None, dry_run=False):
        self.msg = email.parser.BytesParser().parse(sys.stdin.buffer)
        self.dry_run = dry_run
        if logfile is not None:
            self.logfile = open(logfile, 'a+')
        else:
            self.logfile = sys.stdout

        self.now = now = datetime.datetime.now()

        self.msg_id = self.msg['X-Maildrop-Id'] = str(hash(now))

        self.log(('\nDate (datetime.now): {dt_now}'
                  '\nDate (header): {msg["Date"]}'
                  '\nFrom: {msg["From"]}'
                  '\nTo: {msg["To"]}'
                  '\nSubject: {msg["Subject"]}'
                  '\nErrors: {msg.defects}').format(dt_now=now, msg=self.msg))

    def _process_flags(self, flags):
        allowed_flags = {
            'passed': 'P',
            'replied': 'R',
            'seen': 'S',
            'trashed':'T',
            'draft': 'D',
            'flagged': 'F'
        }

        def inner():
            for flag in flags:
                if flag not in allowed_flags:
                    raise RuntimeError('Flag not allowed: {}'.format(flag))

                yield allowed_flags[flag]
        return sorted(inner())

    def drop(self, *folder, **flags):
        folder = pjoin(*folder)
        filename = self.msg_id + ':2,' + ''.join(self._process_flags(flags))
        tmp_path = pjoin(folder, 'tmp', filename)
        new_path = pjoin(folder, 'new', filename)

        self.log(' ===> Writing to {}'.format(new_path))

        if not self.dry_run:
            try:
                self.log('Writing tmpfile to {}'.format(tmp_path))
                with open(tmp_path, 'bw+') as f:
                    gen = email.generator.BytesGenerator(f)
                    gen.flatten(self.msg)

                self.log('Linking tmpfile to newfile')
                os.link(tmp_path, new_path)
            finally:
                self.log('Removing tmpfile')
                os.unlink(tmp_path)

        self.log(' ===> DONE!')
        sys.exit(0)

    def log(self, msg):
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
