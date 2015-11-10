# Copyright 2015 OpenStack LLC.
# All Rights Reserved.
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

import mock

from neutron.common import constants as n_const

from networking_infoblox.neutron.common import constants as const
from networking_infoblox.neutron.common import pattern

from networking_infoblox.tests import base


class TestPatternBuilder(base.TestCase):

    def setUp(self):
        super(TestPatternBuilder, self).setUp()
        self.ib_cxt = self._get_ib_context()
        self.pattern_builder = pattern.PatternBuilder(self.ib_cxt)
        self.test_ip = '11.11.11.11'
        self.expected_ip = self.test_ip.replace('.', '-').replace(':', '-')
        self.expected_domain = (
            self.ib_cxt.grid_config.default_domain_name_pattern.replace(
                '{subnet_id}', self.ib_cxt.subnet['id'])
        )

    def _get_ib_context(self):
        ib_cxt = mock.Mock()
        ib_cxt.network = {'id': 'network-id',
                          'name': 'test-net-1',
                          'tenant_id': 'network-id'}
        ib_cxt.subnet = {'id': 'subnet-id',
                         'name': 'test-sub-1',
                         'tenant_id': 'tenant-id',
                         'network_id': 'network-id'}
        ib_cxt.grid_config.default_host_name_pattern = 'host-{ip_address}'
        ib_cxt.grid_config.default_domain_name_pattern = (
            '{subnet_id}.infoblox.com')
        return ib_cxt

    def _get_test_port(self, device_owner):
        return {'id': 'port-id',
                'device_owner': device_owner,
                'port_id': 'port-id',
                'device_id': 'device-id'}

    def test_get_hostname_for_floating_ip_device_owner(self):
        test_port = self._get_test_port(n_const.DEVICE_OWNER_FLOATINGIP)

        # test with instance name
        instance_name = 'test-vm'
        actual_hostname = self.pattern_builder.get_hostname(
            self.test_ip, instance_name, test_port['id'],
            test_port['device_owner'], test_port['device_id'])
        expected_hostname = str.format("floating-ip-{}.{}", self.expected_ip,
                                       self.expected_domain)
        self.assertEqual(expected_hostname, actual_hostname)

        # test without instance name
        instance_name = None
        actual_hostname = self.pattern_builder.get_hostname(
            self.test_ip, instance_name, test_port['id'],
            test_port['device_owner'], test_port['device_id'])
        expected_hostname = str.format("floating-ip-{}.{}", self.expected_ip,
                                       self.expected_domain)
        self.assertEqual(expected_hostname, actual_hostname)

        # test with instance name pattern
        self.pattern_builder.grid_config.default_host_name_pattern = (
            'host-{instance_name}')
        instance_name = 'test-vm'
        actual_hostname = self.pattern_builder.get_hostname(
            self.test_ip, instance_name, test_port['id'],
            test_port['device_owner'], test_port['device_id'])
        expected_hostname = str.format("host-{}.{}", instance_name,
                                       self.expected_domain)
        self.assertEqual(expected_hostname, actual_hostname)

    def test_get_hostname_for_other_device_owners(self):
        for device in const.NEUTRON_DEVICE_OWNER_TO_PATTERN_MAP:
            test_port = self._get_test_port(device)
            device_pattern = const.NEUTRON_DEVICE_OWNER_TO_PATTERN_MAP[device]
            actual_hostname = self.pattern_builder.get_hostname(
                self.test_ip, None, test_port['id'],
                test_port['device_owner'], test_port['device_id'])
            expected_hostname = str.format(
                "{}.{}", device_pattern.replace('{ip_address}',
                                                self.expected_ip),
                self.expected_domain)
            self.assertEqual(expected_hostname, actual_hostname)

    def test_get_hostname_for_instance_name(self):
        test_port = self._get_test_port('')
        self.pattern_builder.grid_config.default_host_name_pattern = (
            'host-{instance_name}')

        instance_name = 'test.vm'
        actual_hostname = self.pattern_builder.get_hostname(
            self.test_ip, instance_name, test_port['id'],
            test_port['device_owner'], test_port['device_id'])
        expected_instance_name = (
            instance_name.replace('.', '-').replace(':', '-'))
        expected_hostname = str.format("host-{}.{}", expected_instance_name,
                                       self.expected_domain)
        self.assertEqual(expected_hostname, actual_hostname)

    def test_get_zone_name(self):
        # test {subnet_id} pattern
        actual_zone = self.pattern_builder.get_zone_name()
        self.assertEqual(self.expected_domain, actual_zone)

        # test {network_name} pattern
        self.pattern_builder.grid_config.default_domain_name_pattern = (
            '{network_name}.infoblox.com')
        self.expected_domain = (
            self.ib_cxt.grid_config.default_domain_name_pattern.replace(
                '{network_name}', self.ib_cxt.network['name'])
        )
        actual_zone = self.pattern_builder.get_zone_name()
        self.assertEqual(self.expected_domain, actual_zone)

        # test static zone name
        zone = 'infoblox.com'
        self.pattern_builder.grid_config.default_domain_name_pattern = zone
        actual_zone = self.pattern_builder.get_zone_name()
        self.assertEqual(zone, actual_zone)