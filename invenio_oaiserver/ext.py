# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015, 2016 CERN.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Invenio-OAIServer extension implementation."""

from __future__ import absolute_import, print_function

from invenio_records import signals as records_signals

from . import config


class _AppState(object):
    """State for Invenio-OAIServer."""

    def __init__(self, app, cache=None):
        """Initialize state."""
        self.app = app
        self.cache = cache
        if self.app.config['OAISERVER_REGISTER_RECORD_SIGNALS']:
            self.register_signals()

    @property
    def sets(self):
        """Get list of sets."""
        if self.cache:
            return self.cache.get(
                self.app.config['OAISERVER_CACHE_KEY'])

    @sets.setter
    def sets(self, values):
        """Set list of sets."""
        # if cache server is configured, save sets list
        if self.cache:
            self.cache.set(self.app.config['OAISERVER_CACHE_KEY'], values)

    def register_signals(self):
        """Register signals."""
        from .receivers import OAIServerUpdater
        # Register Record signals to update OAI informations
        self.update_function = OAIServerUpdater(app=self.app)
        records_signals.before_record_insert.connect(self.update_function,
                                                     weak=False)
        records_signals.before_record_update.connect(self.update_function,
                                                     weak=False)

    def unregister_signals(self):
        """Unregister signals."""
        # Unregister Record signals
        if hasattr(self, 'update_function'):
            records_signals.before_record_insert.disconnect(
                self.update_function)
            records_signals.before_record_update.disconnect(
                self.update_function)


class InvenioOAIServer(object):
    """Invenio-OAIServer extension."""

    def __init__(self, app=None, **kwargs):
        """Extension initialization."""
        if app:
            self.init_app(app, **kwargs)

    def init_app(self, app, **kwargs):
        """Flask application initialization."""
        self.init_config(app)

        state = _AppState(app=app, cache=kwargs.get('cache'))

        from .views import server  # , settings
        app.register_blueprint(server.blueprint)
        # app.register_blueprint(settings.blueprint)

        app.extensions['invenio-oaiserver'] = state

    def init_config(self, app):
        """Initialize configuration."""
        app.config.setdefault(
            'OAISERVER_BASE_TEMPLATE',
            app.config.get('BASE_TEMPLATE',
                           'invenio_oaiserver/base.html'))

        app.config.setdefault(
            'OAISERVER_REPOSITORY_NAME',
            app.config.get('THEME_SITENAME',
                           'Invenio-OAIServer'))

        # warn user if ID_PREFIX is not set
        if 'OAISERVER_ID_PREFIX' not in app.config:
            import socket
            import warnings

            app.config.setdefault(
                'OAISERVER_ID_PREFIX',
                'oai:{0}:recid/'.format(socket.gethostname()))
            warnings.warn(
                """Please specify the OAISERVER_ID_PREFIX configuration."""
                """default value is: {0}""".format(
                    app.config.get('OAISERVER_ID_PREFIX')))

        for k in dir(config):
            if k.startswith('OAISERVER_'):
                app.config.setdefault(k, getattr(config, k))
