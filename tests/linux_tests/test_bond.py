""" Linux Bond module tests
"""
# disable docstring checking
# pylint: disable=C0111
# disable checking no-self-use
# pylint: disable=R0201
# pylint: disable=W0212
# pylint: disable=W0201
# pylint: disable=F0401
import netshowlib.linux.bond as linux_bond
import mock
from mock import MagicMock
from asserts import assert_equals, mock_open_str
from nose.tools import set_trace


class TestLinuxBondMember(object):
    def setup(self):
        self.bond = linux_bond.Bond('bond0')
        self.iface = linux_bond.BondMember('eth22', master=self.bond)

    def test_showing_master(self):
        assert_equals(self.iface.master, self.bond)

    def test_bondstate(self):
        mock_read_from_sys = MagicMock()
        self.iface.master.read_from_sys = mock_read_from_sys
        mock_read_from_sys.return_value = 'active-backup 2'
        # if lacp is not set and linkstate is not up
        self.iface._linkstate = 1
        assert_equals(self.iface.bondstate, 0)

        # if lacp is not set and linkstate is up
        self.iface._linkstate = 2
        assert_equals(self.iface.bondstate, 1)

        # if lacp is set and agg_id is same
        mock_read_from_sys.return_value = '802.3ad 4'
        bondingfile = open('tests/linux_tests/proc_net_bonding_agg_id_match.txt')
        with mock.patch(mock_open_str()) as mock_open:
            mock_open.return_value = bondingfile
            assert_equals(self.iface.bondstate, 1)

        # if lacp is set and agg_id is different
        bondingfile = open('tests/linux_tests/proc_net_bonding_agg_id_no_match.txt')
        with mock.patch(mock_open_str()) as mock_open:
            mock_open.return_value = bondingfile
            assert_equals(self.iface.bondstate, 0)


class TestLinuxBond(object):
    """ Linux bond tests """

    def setup(self):
        """ setup function """
        self.iface = linux_bond.Bond('bond0')

    @mock.patch('netshowlib.linux.common.read_file_oneline')
    def test_getting_bond_members(self, mock_file_oneline):
        bondmems = 'swp8 swp9'
        # If bond slaves exists
        mock_file_oneline.return_value = bondmems
        assert_equals(sorted(list(self.iface.members.keys())), ['swp8', 'swp9'])
        mock_file_oneline.assert_called_with(
            '/sys/class/net/bond0/bonding/slaves')
        # If bond slaves do not exist
        mock_file_oneline.return_value = None
        assert_equals(self.iface.members, {})

    @mock.patch('netshowlib.linux.common.read_file_oneline')
    def test_get_bond_mode(self, mock_file_oneline):
        mock_file_oneline.return_value = '802.3ad 4'
        assert_equals(self.iface.mode, '4')
        mock_file_oneline.assert_called_with(
            '/sys/class/net/bond0/bonding/mode')
        # test failing to find something
        mock_file_oneline.return_value = None
        assert_equals(self.iface.mode, None)

    @mock.patch('netshowlib.linux.common.read_file_oneline')
    def test_getting_min_links(self, mock_file_oneline):
        mock_file_oneline.return_value = '3'
        assert_equals(self.iface.min_links, '3')
        mock_file_oneline.assert_called_with(
            '/sys/class/net/bond0/bonding/min_links')

    @mock.patch('netshowlib.linux.common.read_file_oneline')
    def test_get_bond_xmit_hash_policy(self, mock_file_oneline):
        mock_file_oneline.return_value = 'layer3+4 1'
        assert_equals(self.iface.hash_policy, '1')
        mock_file_oneline.assert_called_with(
            '/sys/class/net/bond0/bonding/xmit_hash_policy')
        # test failing to find something
        mock_file_oneline.return_value = None
        assert_equals(self.iface.hash_policy, None)

    @mock.patch('netshowlib.linux.lacp.Lacp')
    @mock.patch('netshowlib.linux.common.read_file_oneline')
    def test_get_lacp_instance(self, mock_file_oneline, mock_lacp):
        # test that calling iface.lacp and if iface is LACP
        # creates new Lacp instance
        mock_lacp_instance = mock_lacp.return_value
        mock_file_oneline.return_value = '802.3ad 4'
        assert_equals(self.iface.lacp, mock_lacp_instance)
        mock_file_oneline.assert_called_with(
            '/sys/class/net/bond0/bonding/mode')
        # if bond is not using lacp
        mock_file_oneline.return_value = 'active-backup 1'
        assert_equals(self.iface.lacp, None)

    def test_getting_system_mac(self):
        bondingfile = open('tests/linux_tests/proc_net_bonding.txt')
        with mock.patch(mock_open_str()) as mock_open:
            mock_open.return_value = bondingfile
            assert_equals(self.iface.system_mac, '00:02:00:22:11:33')
