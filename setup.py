from setuptools import setup, find_packages

setup(
    name="deltax-simulator",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'pyserial>=3.5',
    ],
    entry_points={
        'console_scripts': [
            'deltax-simulator=src.simulator.__main__:main',
        ],
    },
) 