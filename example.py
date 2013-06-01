import maildropper
base = '/home/foo/users/mailacc/'

m = maildropper.Maildropper()

# script will exit after m.drop is called

# Mailing Lists
if m.msg.get('Precedence', '').startswith('list'):
    if 'notifications@github.com' in m.msg.get('From', ''):
        if 'markus@unterwaditzer.net' in m.msg.get('Cc', ''):
            m.drop(base, '.INBOX.ml.github', flagged=True)
        m.drop(base, '.INBOX.ml.github')
    m.drop(base, '.INBOX.ml')
