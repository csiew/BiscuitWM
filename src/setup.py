from setuptools import setup
from setuptools.command.install import install
import os


class MyInstall(install):
    def run(self):
        install.run(self)
        os.system('sudo sh scripts/setup.sh')


setup(
    name='BiscuitWM',
    version='0.1',
    packages=['BiscuitWM'],
    package_dir={'': 'src'},
    url='https://github.com/csiew/BiscuitWM',
    license='',
    author='csiew',
    author_email='',
    description='The weirdly delectable window manager',
    install_requires=['python-xlib', 'x11util', 'perlcompat', 'ewmh', 'Xlib'],
    scripts=['scripts/setup.sh', 'scripts/purge.sh'],
    cmdclass={'install': MyInstall}
)
