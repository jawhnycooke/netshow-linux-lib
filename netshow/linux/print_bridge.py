# pylint: disable=E0611
"""
Print and Analysis Module for Linux bridge interfaces
"""
from netshow.linux.print_iface import PrintIface
from netshowlib.linux import common
from tabulate import tabulate
from netshow.linux.common import _
import inflection

class PrintBridgeMember(PrintIface):
    """
    Print and Analysis Class for Linux bridge member interfaces
    """
    @property
    def port_category(self):
        """
        :return: port category for bridge member
        """
        if self.iface.is_trunk():
            return _('trunk/l2')
        return _('access/l2')

    @property
    def summary(self):
        """
        :return: summary info regarding a bridge member
        """
        if self.iface.is_trunk():
            return self.trunk_summary()
        return self.access_summary()

    def cli_output(self):
        """
        :return: output for 'netshow interface <ifacename> for a bridge interface'
        """
        _str = self.cli_header()
        _str += self.bridgemem_details()
        _str += self.lldp_details()

        return _str


class PrintBridge(PrintIface):
    """
    Print and Analysis Class for Linux bridge interfaces
    """
    @property
    def port_category(self):
        """
        :return: port category of bridge. Then return its a L2 or L3 port as wel
        """
        if self.iface.is_l3():
            return _('bridge/l3')
        return _('bridge/l2')

    @property
    def summary(self):
        """
        :return: summary information regarding the bridge
        """
        _info = []
        _info.append(self.untagged_ifaces())
        _info.append(self.tagged_ifaces())
        _info.append(self.vlan_id_field())
        _info.append(self.stp_summary())
        return [x for x in _info if x]

    def untagged_ifaces(self):
        """
        :return: list of untagged interfaces of the bridge
        """
        _untagmems = self.iface.untagged_members.keys()
        if _untagmems:
            _str = "%s:" % (_('untagged'))
            _str += ' ' + ','.join(common.group_ports(_untagmems))
            return _str
        return ''

    def tagged_ifaces(self):
        """
        :return: list of tagged interfaces of the bridge
        """
        _tagmems = self.iface.tagged_members.keys()
        if _tagmems:
            _str = "%s:" % (_('tagged'))
            _str += ' ' + ','.join(common.group_ports(_tagmems))
            return _str
        return ''

    def vlan_id(self):
        """
        :return: vlan id
        :return: 'untagged' if non is available
        """
        _vlantag = self.iface.vlan_tag
        if _vlantag:
            _str = ','.join(_vlantag)
        else:
            _str = _('untagged')
        return _str

    def vlan_id_field(self):
        """
        return: list with label saying 'vlan id' and vlan tag
        """
        _str = "%s: %s" % (_('802.1q_tag'), self.vlan_id())
        return _str

    def stp_summary(self):
        """
        :return: root switch priority if switch is root of bridge
        :return: root port if switch is not root of bridge
        :return: stp disabled if stp is disabled
        """
        _str = ["%s:" % (_('stp'))]
        if self.iface.stp:
            if self.iface.stp.is_root():
                _str.append("%s(%s)" % (_('rootswitch'),
                                        self.iface.stp.root_priority))
            else:
                _str.append("%s(%s)" % (','.join(self.root_port()),
                                        _('root')))
                _str.append("%s(%s)" % (self.iface.stp.root_priority,
                                        _('root_priority')))
        else:
            _str.append(_('disabled'))
        return ' '.join(_str)

    def root_port(self):
        """
        return: root port (should be only one or None)
        """
        _root_ports = self.iface.stp.member_state.get('root')
        # should be only one..but just in case something is messed up
        # print all root ports found
        _rootportnames = []
        for _port in _root_ports:
            _rootportnames.append(_port.name)
        return _rootportnames

    def stp_details(self):
        """
        :return: stp details for the bridge interface
        """
        _header = [_(''), '']
        _table = []
        _table.append([_('stp_mode') + ':', _('802.1d / per bridge instance')])
        _table.append([_('root_port') + ':', ', '.join(self.root_port())])
        _table.append([_('root_priority') + ':', self.iface.stp.root_priority])
        _table.append([_('bridge_priority') + ':', self.iface.stp.bridge_priority])
        _table.append(self.vlan_id_field().split())
        return tabulate(_table, _header)

    def no_stp_details(self):
        """
        :return: details when stp is not enabled
        """
        _header = ['', '']
        _table = []
        _table.append([_('stp_mode') + ':', _('disabled')])
        _table.append(self.vlan_id_field().split())
        return tabulate(_table, _header) + self.new_line()

    def ports_of_some_kind_of_state(self, statename):
        _header = [_("ports in %s state") %
                   (inflection.titleize(statename))]
        _table = []
        _portlist = [_x.name for _x in
                     self.iface.stp.member_state.get(statename)]
        if _portlist:
            _table.append([', '.join(common.group_ports(_portlist))])
            return tabulate(_table, _header)
        return ''

    def cli_output(self):
        """
        :return: output for 'netshow interface <ifacename> for a bridge interface'
        """
        _str = self.cli_header() + self.new_line()
        _str += self.ip_details() + self.new_line()
        if self.iface.stp:
            _str += self.stp_details() + self.new_line()
            for _state in ['forwarding', 'blocking']:
                _str += self.ports_of_some_kind_of_state(_state) + \
                    self.new_line()
        else:
            _str += self.no_stp_details() + self.new_line()

        return _str
