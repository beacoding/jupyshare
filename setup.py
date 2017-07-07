from setuptools import setup, find_packages

setup(
        name='jupyshare',
        version='1.0.3',
        entry_points = {
            'console_scripts': ['jupyshare=jupyshare.share:main']
            },
        packages=find_packages(),
        author='bianca subion',
        author_email='bianca.subion@gmail.com',
        description='Share your python notebooks in the cloud',
        url='https://github.com/biancasubion/jupyshare',
        download_url='https://github.com/biancasubion/jupyshare/archive/1.0.3.tar.gz',
        keywords=['jupyter', 'notebook', 'share'],
        install_requires=[
            'args==0.1.0',
            'clint==0.5.1',
            'requests==2.13.0'
            ],
        )
