# Copyright (c) 2020, 2021, 2022 Humanitarian OpenStreetMap Team
# This file is part of FMTM.
#
#     FMTM is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     FMTM is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with FMTM.  If not, see <https:#www.gnu.org/licenses/>.
#

import sqlite3

import pytest

from src.db import get_db
from src.models import User

# def test_get_close_db(app):
#    with app.app_context():
#        db = get_db()
#        assert db is get_db()
#    with pytest.raises(sqlite3.ProgrammingError) as e: db.session.query(User).first()
#    assert 'closed' in str(e.value)
#
# def test_init_db_command(runner, monkeypatch):
#    class Recorder(object):
#        called = False
#
#    def fake_init_db():
#        Recorder.called = True
#
#    monkeypatch.setattr('src/web.db.init_db', fake_init_db)
#    result = runner.invoke(args=['init-db'])
#    assert 'Initialized' in result.output
#    assert Recorder.called
