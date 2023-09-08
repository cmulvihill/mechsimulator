""" Install mechsimulator functions
"""

from distutils.core import setup


setup(
    name="mechsimulator",
    version="0.1.0",
    packages=[
        'parser',
        'plotter',
        'runner',
        'simulator',
        'writer',
    ],
    package_data={
        'tests': [
            'data/*',
        ]
    }
)
