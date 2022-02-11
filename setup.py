# -*- coding: utf-8 -*-
#
# Copyright © 2021 Genome Research Ltd. All rights reserved.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# @author Keith James <kdj@sanger.ac.uk>

from setuptools import find_packages, setup

setup(
    name="npg-metadata-sync",
    url="https://github.com/kjsanger/npg-metadata-sync",
    license="GPL3",
    author="Keith James",
    author_email="kdj@sanger.ac.uk",
    description=".",
    use_scm_version=True,
    python_requires=">=3.9",
    packages=find_packages("src"),
    package_dir={"": "src"},
    setup_requires=["setuptools_scm"],
    install_requires=[
        "ml-warehouse",
        "partisan",
    ],
    tests_require=["pytest"],
)
