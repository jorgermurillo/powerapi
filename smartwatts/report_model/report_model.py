# Copyright (C) 2018  University of Lille
# Copyright (C) 2018  INRIA
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Module report_model
"""

KEYS_COMMON = ['timestamp', 'sensor', 'target']
KEYS_CSV_COMMON = KEYS_COMMON + ['socket', 'cpu']


class ReportModel:
    """
    ReportModel class.
    It define all the function that need to be override if we want
    to get a report from every kind of db.
    """

    def from_mongodb(self, json):
        """ get the mongodb report """
        raise NotImplementedError()

    def from_csvdb(self, file_name, row):
        """ get the csvdb report """
        raise NotImplementedError()
