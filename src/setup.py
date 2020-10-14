from setuptools import setup
from setuptools.command.install import install
import os


class MyInstall(install):
    def run(self):
        install.run(self)
        os.system('sudo sh scripts/biscuitwm-install.sh')


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
    install_requires=['python-xlib', 'x11util', 'perlcompat', 'ewmh'],
    scripts=['scripts/biscuitwm-install.sh', 'scripts/biscuitwm-uninstall.sh'],
    cmdclass={'install': MyInstall}
)
