# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015, 2016 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
# -*- coding: utf-8 -*-
#
# In applying this licence, CERN does not waive the privileges and immunities
# granted to it by virtue of its status as an Intergovernmental Organization
# or submit itself to any jurisdiction.

"""Percolator test cases."""

from invenio_db import db
from invenio_records.api import Record

from invenio_oaiserver import current_oaiserver
from invenio_oaiserver.models import OAISet


def test_without_percolator(app, request):
    """Test percolator."""
    with app.test_request_context():
        current_oaiserver.unregister_signals()
        current_oaiserver.register_signals()

        _try_populate_oaisets()


def _try_populate_oaisets():
    """Try to update collections."""
    schema = {
        'type': 'object',
        'properties': {
                'title': {'type': 'string'},
                'field': {'type': 'boolean'},
            },
        'required': ['title'],
    }

    a = OAISet(name="a")
    b = OAISet(name="b")
    e = OAISet(
        name="e", search_pattern="title:Test2 OR title:Test3")
    c = OAISet(name="c", search_pattern="title:Test0")
    d = OAISet(name="d", search_pattern="title:Test1")
    f = OAISet(name="f", search_pattern="title:Test2")
    g = OAISet(name="g")
    h = OAISet(name="h")
    i = OAISet(name="i", search_pattern="title:Test3")
    j = OAISet(name="j", search_pattern="title:Test4")

    with db.session.begin_nested():
        for coll in [a, b, c, d, e, f, g, h, i, j]:
            db.session.add(coll)

    db.session.commit()

    # start tests

    record0 = Record.create({'title': 'Test0', '$schema': schema})

    assert 'c' in record0['_oaisets']
    assert len(record0['_oaisets']) == 1

    record = Record.create({'title': 'TestNotFound', '$schema': schema})

    assert record['_oaisets'] == []

    record = Record.create({'title': 'Test1', '$schema': schema})

    assert 'd' in record['_oaisets']
    assert len(record['_oaisets']) == 1

    record = Record.create({'title': 'Test2', '$schema': schema})

    assert 'e' in record['_oaisets']
    assert 'f' in record['_oaisets']
    assert len(record['_oaisets']) == 2

    record3 = Record.create({'title': 'Test3', '$schema': schema})

    assert 'e' in record3['_oaisets']
    assert 'i' in record3['_oaisets']
    assert len(record3['_oaisets']) == 2

    record4 = Record.create({'title': 'Test4', '$schema': schema})

    assert 'j' in record4['_oaisets']
    assert len(record4['_oaisets']) == 1

    # test delete
    db.session.delete(j)
    db.session.commit()
    record4.commit()

    assert 'h' not in record4['_oaisets']
    assert 'j' not in record4['_oaisets']
    assert len(record4['_oaisets']) == 0

    # test update search_pattern
    i.search_pattern = None
    db.session.add(i)
    db.session.commit()
    record3.commit()

    assert 'e' in record3['_oaisets']
    assert len(record3['_oaisets']) == 1

    # test update search_pattern
    i.search_pattern = 'title:Test3'
    db.session.add(i)
    db.session.commit()
    record3.commit()

    assert 'e' in record3['_oaisets']
    assert 'i' in record3['_oaisets']
    assert len(record3['_oaisets']) == 2

    # test update name
    a.name = "new-a"
    db.session.add(a)
    db.session.commit()
    record3.commit()

    assert 'i' in record3['_oaisets']
    assert 'e' in record3['_oaisets']
    assert len(record3['_oaisets']) == 2

    # test update name
    c.name = "new-c"
    db.session.add(c)
    db.session.commit()
    record0.commit()

    assert 'new-c' in record0['_oaisets']
    assert len(record0['_oaisets']) == 1
