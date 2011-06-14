import os
import platform 

CONFIG_DIR = os.path.expanduser('~/.dotcloud')
CONFIG_FILE = os.path.basename(os.environ.get('DOTCLOUD_CONFIG_FILE', 'dotcloud.conf'))
CONFIG_PATH = os.path.join(CONFIG_DIR, CONFIG_FILE)
if 'DOTCLOUD_CONFIG_FILE' in os.environ:
    CONFIG_KEY = CONFIG_PATH + '.key'
else:
    CONFIG_KEY = os.path.join(CONFIG_DIR, 'dotcloud.key')

CONFIG_KEY = '"' + CONFIG_KEY + '"'

print CONFIG_KEY