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
import re
from datetime import datetime
from itertools import starmap
from os import PathLike
from pathlib import PurePath
from typing import List, Tuple, Union

from partisan.irods import AC, AVU, Collection, Permission
from partisan.metadata import DublinCore
from sqlalchemy import asc, distinct
from sqlalchemy.orm import Session
from structlog import get_logger

import ont
from metadata import ONTInstrument, TrackedSample, TrackedStudy

from ml_warehouse.schema import OseqFlowcell, Sample, Study

log = get_logger(__package__)

TAG_IDENTIFIER_REGEX = re.compile(r"-(?P<tag_index>\d+)$")


def tag_index(tag_identifier: str) -> int:
    """ "Returns the barcode tag index given a barcode tag identifier.

    Returns: int
    """
    match = TAG_IDENTIFIER_REGEX.search(tag_identifier)
    if match:
        return int(match.group("tag_index"))

    raise ValueError(
        f"Invalid ONT tag identifier '{tag_identifier}'. "
        f"Expected a value matching {TAG_IDENTIFIER_REGEX}"
    )


def barcode_name(tag_identifier: str) -> str:
    """Returns the barcode name given a barcode tag identifier. The name is used most
    often for directory naming in ONT experiment results.

    Returns: str
    """
    match = TAG_IDENTIFIER_REGEX.search(tag_identifier)
    if match:
        return "barcode{}".format(match.group("tag_index").zfill(2))

    raise ValueError(
        f"Invalid ONT tag identifier '{tag_identifier}'. "
        f"Expected a value matching {TAG_IDENTIFIER_REGEX}"
    )


def annotate_results_collection(
    path: Union[str, PathLike],
    experiment_name: str,
    instrument_slot: int,
    mlwh_session: Session,
):
    log.debug(
        "Searching the warehouse for plex information",
        experiment=experiment_name,
        slot=instrument_slot,
    )

    plex_info = find_ont_plex_info(mlwh_session, experiment_name, instrument_slot)

    avus = [
        AVU(ONTInstrument.EXPERIMENT_NAME, experiment_name),
        AVU(ONTInstrument.INSTRUMENT_SLOT, instrument_slot),
    ]
    avus = [avu.with_namespace(ONTInstrument.namespace) for avu in avus]

    coll = Collection(path)
    coll.add_metadata(*avus)  # These AVUs should be present already

    # There will be either a single fc record (for un-plexed data) or
    # multiple (one per plex of multiplexed data)
    for fc in plex_info:
        log.debug(
            "Found experiment /slot / tag index",
            experiment=experiment_name,
            slot=instrument_slot,
            tag_identifier=fc.tag_identifier,
        )

        if fc.tag_identifier:
            # This is the barcode directory naming style created by ONT's
            # Guppy and qcat de-plexers. We add information to the
            # barcode sub-collection.
            p = PurePath(path) / barcode_name(fc.tag_identifier)
            log.debug("Annotating iRODS path", path=p, tag_identifier=fc.tag_identifier)
            log.debug("Annotating iRODS path", path=p, sample=fc.sample, study=fc.study)

            coll = Collection(p)
            coll.add_metadata(AVU("tag_index", ont.tag_index(fc.tag_identifier)))
            coll.add_metadata(*make_study_metadata(fc.study))
            coll.add_metadata(*make_sample_metadata(fc.sample))

            # The ACL could be different for each plex
            coll.add_permissions(*make_sample_acl(fc.sample, fc.study), recurse=True)
        else:
            # There is no tag index, meaning that this is not a
            # multiplexed run, so we add information to the containing
            # collection.
            coll.add_metadata(*make_study_metadata(fc.study))
            coll.add_metadata(*make_sample_metadata(fc.sample))

            coll.add_permissions(*make_sample_acl(fc.sample, fc.study), recurse=True)


def make_creation_metadata(creator: str, created: datetime):
    """Returns standard iRODS metadata for data creation:

      - creator
      - created

    Args:
        creator: name of user or service creating data
        created: creation timestamp

    Returns: List[AVU]
    """
    return [
        AVU(DublinCore.CREATOR.value, creator, namespace=DublinCore.namespace),
        AVU(
            DublinCore.CREATED.value,
            created.isoformat(timespec="seconds"),
            namespace=DublinCore.namespace,
        ),
    ]


def make_modification_metadata(modified: datetime):
    return [
        AVU(
            DublinCore.MODIFIED.value,
            modified.isoformat(timespec="seconds"),
            namespace=DublinCore.namespace,
        )
    ]


def avu_if_value(attribute, value):
    if value is not None:
        return AVU(attribute, value)


def make_sample_metadata(sample: Sample) -> List[AVU]:
    """Returns standard iRODS metadata for a Sample:

     - sample ID
     - sample name
     - sample accession
     - sample donor ID
     - sample supplier name
     - sample consent withdrawn

    Args:
        sample: An ML warehouse schema Sample.

    Returns: List[AVU]
    """
    av = [
        [TrackedSample.ID, sample.sanger_sample_id],
        [TrackedSample.NAME, sample.name],
        [TrackedSample.ACCESSION_NUMBER, sample.accession_number],
        [TrackedSample.DONOR_ID, sample.donor_id],
        [TrackedSample.SUPPLIER_NAME, sample.supplier_name],
        [
            TrackedSample.CONSENT_WITHDRAWN,
            1 if sample.consent_withdrawn else None,
        ],
    ]

    return list(filter(lambda avu: avu is not None, starmap(avu_if_value, av)))


def make_study_metadata(study: Study):
    av = [
        [TrackedStudy.ID, study.id_study_lims],
        [TrackedStudy.NAME, study.name],
        [TrackedStudy.ACCESSION_NUMBER, study.accession_number],
    ]

    return list(filter(lambda avu: avu is not None, starmap(avu_if_value, av)))


def make_sample_acl(sample: Sample, study: Study) -> List[AC]:
    irods_group = f"ss_{study.id_study_lims}"
    perm = Permission.NULL if sample.consent_withdrawn else Permission.READ

    return [AC(irods_group, perm)]


def find_recent_ont_expt(session: Session, since: datetime) -> List[str]:
    """Finds recent ONT experiments in the ML warehouse database.

    Finds ONT experiments in the ML warehouse database that have been updated
    since a specified date and time. If any element of the experiment (any of
    the positions in a multi-flowcell experiment, any of the multiplexed
    elements within a position) have been updated in the query window, the
    experiment name will be returned.

    Args:
        session: An open SQL session.
        since: A datetime.

    Returns:
        List of matching experiment name strings
    """

    result = (
        session.query(distinct(OseqFlowcell.experiment_name))
        .filter(OseqFlowcell.last_updated >= since)
        .all()
    )

    # The default behaviour of SQLAlchemy is that the result here is a list
    # of tuples, each of which must be unpacked. The official way to do
    # that for all cases is to extend sqlalchemy.orm.query.Query to do the
    # unpacking. However, that's too fancy for MVP, so we just unpack
    # manually.
    return [value for value, in result]


def find_recent_ont_pos(session: Session, since: datetime) -> List[Tuple]:
    """Finds recent ONT experiments and instrument positions in the ML
    warehouse database.

    Finds ONT experiments and associated instrument positions in the ML
    warehouse database that have been updated since a specified date and time.

    Args:
        session: An open SQL session.
        since: A datetime.

    Returns:
        List of matching (experiment name, position) tuples
    """

    return (
        session.query(OseqFlowcell.experiment_name, OseqFlowcell.instrument_slot)
        .filter(OseqFlowcell.last_updated >= since)
        .group_by(OseqFlowcell.experiment_name, OseqFlowcell.instrument_slot)
        .order_by(asc(OseqFlowcell.experiment_name), asc(OseqFlowcell.instrument_slot))
        .all()
    )


def find_ont_plex_info(
    session: Session, experiment_name: str, instrument_slot: int
) -> List[OseqFlowcell]:
    flowcells = (
        session.query(OseqFlowcell)
        .filter(
            OseqFlowcell.experiment_name == experiment_name,
            OseqFlowcell.instrument_slot == instrument_slot,
        )
        .order_by(
            asc(OseqFlowcell.experiment_name),
            asc(OseqFlowcell.instrument_slot),
            asc(OseqFlowcell.tag_identifier),
            asc(OseqFlowcell.tag2_identifier),
        )
        .all()
    )

    return flowcells
