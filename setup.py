# coding: utf-8
try:
    from setuptools import setup, find_packages
except ImportError:
    import distribute_setup
    distribute_setup.use_setuptools()
    from setuptools import setup, find_packages


setup(
    name='MPDC',
    version='1.1',
    license='MIT',
    description='A XMMS2-like collections system for MPD, aimed at '
                'helping you to feed and manipulate your playlist with '
                'great flexibility',
    author='nhrx.org',
    url='http://nhrx.org/mpdc',
    packages=find_packages(),
    entry_points={
          'console_scripts': [
              'mpdc = mpdc.mpdc_cli:main',
          ]
    },
    install_requires=['ply >= 3.4', 'python-mpd2 >= 0.4.0']
)
