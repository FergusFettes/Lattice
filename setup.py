import setuptools

with open('README.md', 'r') as fh:
    long_description = fh.read()

setuptools.setup(
    name='LatticeModelMashup',
    version='0.98.1',
    packages=['latticeModelMashup',],
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/fergusfettes/lattice',
    author='Fergus Fettes',
    author_email='fergusfettes@gmail.com',
    description='An ungodly mixture of lattice models',
    install_requires=[
        'imageio',
        'numpy',
        'PyQt5',
        'ffmpeg',
    ],
    classifiers=[
        'Programming Language :: Python :: 3.6',
        'Topic :: Games/Entertainment :: Simulation',
        'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',
        'Development Status :: 4 - Beta',
        'Operating System :: POSIX :: Linux',
    ],
    entry_points={
        'console_scripts': [
            'latticeMash = latticeModelMashup.__init__:main',
        ],
    },
)
