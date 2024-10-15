from setuptools import find_packages
from setuptools import setup

setup(
    name='SalvatoreSortingSoftware',
    version='1.0.0',
    description='Software to merge important information from Club Assist E-Invoice to GoPayment for Quickbooks invoicing',
    author='Parker Miconi',
    author_email='parkermiconi@gmail.com',
    url='',
    package_data={
        'sss_package': ['creds.json', 'logo.jpeg'],
    },
    install_requires=['customtkinter',
                      'fuzzywuzzy',
                      'gspread',
                      'gspread_formatting',
                      'oauth2client',
                      'pandas',
                      'Pillow',
                      'setuptools',
                      'pyinstaller'
    ],
    packages=find_packages(),
    entry_points={
        'console_scripts':[
            'sss_run = sss_package.main:main'
        ],
    }
)