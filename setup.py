import os
from setuptools import setup
from  packetpusher import __version__ as version
setup(
    name = "packetpusher",
    version = version,
    author = "Rafael Ferreira",
    author_email = "raf@ophion.org",
    description = ('Packet Pusher - Network speed tester'),
    license =  'MIT/X11',
    keywords = "password encryption rsa",
    url = "https://github.com/rferreira/packetpusher",
    packages=['packetpusher'],
    long_description='simple network performance tester',
    classifiers=[
        'Development Status :: 4 - Beta',
        "Topic :: Utilities",
        'License :: OSI Approved :: Apache Software License'
    ],
    install_requires=['prettytable'],
    scripts=['scripts/packetpusher.py']
)
