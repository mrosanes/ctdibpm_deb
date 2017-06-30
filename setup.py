#!/usr/bin/env python

# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 3
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

__author__ = "Jairo Moldes"
__copyright__ = "Copyright 2015, CELLS / ALBA Synchrotron"
__license__ = "GPLv3+"

# The version is updated automatically with bumpversion
# Do not update manually
__version = '1.1.1'  


from setuptools import setup, find_packages

setup(
    name="ctdibpm",
    license=__license__, 
    version=__version,    
    author="Jairo Moldes",
    author_email="jmoldes@cells.es",
    maintainer='ct4',
    maintainer_email='ct4@cells.es',
    packages=find_packages(),
    entry_points={
        'console_scripts': [],
        'gui_scripts': [
            'ctdibpm = ctdibpm.ctdibpm:main',
            ]
        },
    options={
        'build_scripts': {
                'executable': '/usr/bin/env python',
                    },
        },
    keywords='GUI',
    include_package_data=True,
    description="GUI for BPM Configuration",
    long_description="Graphical User Interface for Beam Position Monitor "
    "Configuration",
    requires=['setuptools (>=1.1)'],
    classifiers=['Development Status :: 5 - Production',
                 'Intended Audience :: Science/Research',
                 'License :: OSI Approved :: '
                 'GNU General Public License v3 or later (GPLv3+)',
                 'Programming Language :: Python',
                 'Topic :: Scientific/Engineering :: '
                 ''],
    url="https://git.cells.es/controls/ctdibpm",
)

