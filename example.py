import maildropper
base = '/home/foo/users/mailacc/'

m = maildropper.Maildropper()

# script will exit after m.drop is called

# Mailing Lists
if m.header('Precedence').startswith('list'):
    if 'notifications@github.com' in m.header('From'):
        if 'markus@unterwaditzer.net' in m.header('Cc'):
            m.drop(base, '.INBOX.ml.github', flagged=True)
        m.drop(base, '.INBOX.ml.github')
    m.drop(base, '.INBOX.ml')
