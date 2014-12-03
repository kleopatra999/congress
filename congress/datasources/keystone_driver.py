#!/usr/bin/env python
# Copyright (c) 2014 VMware, Inc. All rights reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
#
import keystoneclient.v2_0.client

from congress.datasources.datasource_driver import DataSourceDriver
from congress.datasources import datasource_utils


def d6service(name, keys, inbox, datapath, args):
    """This method is called by d6cage to create a dataservice instance."""
    d = KeystoneDriver(name, keys, inbox, datapath, args)
    return d


class KeystoneDriver(DataSourceDriver):
    # Table names
    USERS = "users"
    ROLES = "roles"
    TENANTS = "tenants"

    # This is the most common per-value translator, so define it once here.
    value_trans = {'translation-type': 'VALUE'}

    users_translator = {
        'translation-type': 'HDICT',
        'table-name': USERS,
        'selector-type': 'DOT_SELECTOR',
        'field-translators':
            ({'fieldname': 'username', 'translator': value_trans},
             {'fieldname': 'name', 'translator': value_trans},
             {'fieldname': 'enabled', 'translator': value_trans},
             {'fieldname': 'tenantId', 'translator': value_trans},
             {'fieldname': 'id', 'translator': value_trans},
             {'fieldname': 'email', 'translator': value_trans})}

    roles_translator = {
        'translation-type': 'HDICT',
        'table-name': ROLES,
        'selector-type': 'DOT_SELECTOR',
        'field-translators':
            ({'fieldname': 'id', 'translator': value_trans},
             {'fieldname': 'name', 'translator': value_trans})}

    tenants_translator = {
        'translation-type': 'HDICT',
        'table-name': TENANTS,
        'selector-type': 'DOT_SELECTOR',
        'field-translators':
            ({'fieldname': 'enabled', 'translator': value_trans},
             {'fieldname': 'description', 'translator': value_trans},
             {'fieldname': 'name', 'translator': value_trans},
             {'fieldname': 'id', 'translator': value_trans})}

    def __init__(self, name='', keys='', inbox=None, datapath=None, args=None):
        super(KeystoneDriver, self).__init__(name, keys, inbox, datapath, args)
        self.register_translator(KeystoneDriver.users_translator)
        self.register_translator(KeystoneDriver.roles_translator)
        self.register_translator(KeystoneDriver.tenants_translator)
        self.creds = self.get_keystone_credentials_v2(name, args)
        self.client = keystoneclient.v2_0.client.Client(**self.creds)

    def get_keystone_credentials_v2(self, name, args):
        creds = datasource_utils.get_credentials(name, args)
        d = {}
        d['version'] = '2'
        d['username'] = creds['username']
        d['password'] = creds['password']
        d['auth_url'] = creds['auth_url']
        d['tenant_name'] = creds['tenant_name']
        return d

    def update_from_datasource(self):
        row_data = []
        row_data.extend(KeystoneDriver.convert_objs(
            self.client.users.list(),
            KeystoneDriver.users_translator))
        row_data.extend(KeystoneDriver.convert_objs(
            self.client.roles.list(),
            KeystoneDriver.roles_translator))
        row_data.extend(KeystoneDriver.convert_objs(
            self.client.tenants.list(),
            KeystoneDriver.tenants_translator))

        # TODO(alexsyip): make DataSourceDriver do this.
        new_state = {}
        for table, row in row_data:
            if table not in new_state:
                new_state[table] = set()
            new_state[table].add(row)
        self.state = new_state


def main():
    print('Schema:')
    print('\n'.join([k + ' ' + str(v)
                     for k, v in KeystoneDriver.get_schema().items()]))


if __name__ == '__main__':
    try:
        main()
    except SystemExit:
        # Let system.exit() calls complete normally
        raise
    except Exception:
        raise
