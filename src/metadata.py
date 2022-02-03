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

from enum import unique

from partisan.metadata import AsValueEnum, with_namespace


@unique
class TrackedSample(AsValueEnum):
    """SequenceScape Sample metadata."""

    ACCESSION_NUMBER = "sample_accession_number"
    COHORT = "sample_cohort"
    COMMON_NAME = "sample_common_name"
    CONSENT = "sample_consent"
    CONSENT_WITHDRAWN = "sample_consent_withdrawn"
    CONTROL = "sample_control"
    DONOR_ID = "sample_donor_id"
    ID = "sample_id"
    NAME = "sample"
    PUBLIC_NAME = "sample_public_name"
    SUPPLIER_NAME = "sample_supplier_name"

    def __str__(self):
        return str(self.__repr__())


@unique
class TrackedStudy(AsValueEnum):
    """SequenceScape Study metadata."""

    ACCESSION_NUMBER = "study_accession_number"
    ID = "study_id"
    NAME = "study"
    TITLE = "study_title"

    def __str__(self):
        return str(self.__repr__())


@unique
class ONTInstrument(str, AsValueEnum, metaclass=with_namespace("ont")):
    """Oxford Nanopore platform metadata"""

    EXPERIMENT_NAME = "experiment_name"
    INSTRUMENT_SLOT = "instrument_slot"

    def __str__(self):
        return str(self.__repr__())
