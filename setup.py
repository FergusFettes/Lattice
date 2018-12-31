import setuptools

with open('README.md', 'r') as fh:
    long_description = fh.read()

setuptools.setup(
    name='LatticeModelMashup',
    version='0.95',
    packages=['latticeModelMashup',],
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/fergusfettes/lattice',
    author='Fergus Fettes',
    author_email='fergusfettes@gmail.com',
    description='An ungodly mixture of lattice models',
    classifiers=[
        'Programming Language :: Python :: 3.6',
        'Topic :: Games/Entertainment :: Simulation',
        'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',
        'Development Status :: 4 - Beta',
        'Operating System :: POSIX :: Linux',
    ],
)
