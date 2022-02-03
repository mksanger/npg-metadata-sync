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

from partisan.irods import AC, AVU, Collection, Permission
from pytest import mark as m

import ont
from conftest import icommands_have_admin
from ont import annotate_results_collection


class TestONT(object):
    @icommands_have_admin
    @m.context("When an ONT experiment collection is annotated")
    @m.context("When the experiment is single-sample")
    @m.it("Adds sample and study metadata to the run-folder collection")
    def test_add_new_sample_metadata(self, ont_synthetic, mlwh_session):
        expt = "simple_experiment_001"
        pos = 1

        path = ont_synthetic / expt / "20190904_1514_GA10000_flowcell011_69126024"
        annotate_results_collection(
            path, experiment_name=expt, instrument_slot=pos, mlwh_session=mlwh_session
        )

        coll = Collection(path)
        for avu in [
            AVU("sample", "sample 1"),
            AVU("study_id", "study_02"),
            AVU("study", "Study Y"),
        ]:
            assert avu in coll.metadata(), f"{avu} is in {coll} metadata"

        ac = AC("ss_study_02", Permission.READ, zone="testZone")
        assert ac in coll.acl()
        for item in coll.contents():
            assert ac in item.acl(), f"{ac} is in {item} ACL"

    @icommands_have_admin
    @m.context("When the experiment is multiplexed")
    @m.it("Adds {tag_index => <n>} metadata to barcode<0n> sub-collections")
    def test_add_new_plex_metadata(self, ont_synthetic, mlwh_session):
        expt = "multiplexed_experiment_001"
        pos = 1

        path = ont_synthetic / expt / "20190904_1514_GA10000_flowcell101_cf751ba1"

        annotate_results_collection(
            path, experiment_name=expt, instrument_slot=pos, mlwh_session=mlwh_session
        )

        for tag_index in range(1, 12):
            tag_identifier = f"ONT-Tag-Identifier-{tag_index}"
            bc_coll = Collection(path / ont.barcode_name(tag_identifier))
            avu = AVU("tag_index", ont.tag_index(tag_identifier))
            assert avu in bc_coll.metadata(), f"{avu} is in {bc_coll} metadata"

    @icommands_have_admin
    @m.it("Adds sample and study metadata to barcode<0n> sub-collections")
    def test_add_new_plex_sample_metadata(self, ont_synthetic, mlwh_session):
        expt = "multiplexed_experiment_001"
        pos = 1

        path = ont_synthetic / expt / "20190904_1514_GA10000_flowcell101_cf751ba1"

        annotate_results_collection(
            path, experiment_name=expt, instrument_slot=pos, mlwh_session=mlwh_session
        )

        for tag_index in range(1, 12):
            bc_coll = Collection(
                path / ont.barcode_name(f"ONT-Tag-Identifier-{tag_index}")
            )

            for avu in [
                AVU("sample", f"sample {tag_index}"),
                AVU("study_id", "study_03"),
                AVU("study", "Study Z"),
            ]:
                assert avu in bc_coll.metadata(), f"{avu} is in {bc_coll} metadata"

            ac = AC("ss_study_03", Permission.READ, zone="testZone")
            assert ac in bc_coll.acl(), f"{ac} is in {bc_coll} ACL"
            for item in bc_coll.contents():
                assert ac in item.acl(), f"{ac} is in {item} ACL"
