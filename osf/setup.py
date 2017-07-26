from setuptools import setup, find_packages

setup(
    name='osf',
    version='0.0.3',
    description='python interface to different feeds',
    url='https://github.com/mhfowler/open-source-feeds',
    author='Max Fowler (@notplants)',
    license='MIT',

    packages=find_packages(),
    install_requires=[
        'requests',
        'selenium'
    ]
)