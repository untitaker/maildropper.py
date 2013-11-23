import maildropper
m = Maildropper('user', 'pwd', 'example.com')  # IMAP over SSL

# script will exit after m.drop is called

# Mailing Lists
if m.header('Precedence').startswith('list'):
    if 'notifications@github.com' in m.header('From'):
        if 'markus@unterwaditzer.net' in m.header('Cc'):
            m.drop('INBOX.ml.github', flagged=True)
        m.drop('INBOX.ml.github')
    m.drop('INBOX.ml')
