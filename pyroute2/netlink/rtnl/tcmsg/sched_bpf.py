'''
'''

from pyroute2.netlink import nla
from pyroute2.netlink.rtnl import TC_H_ROOT
from pyroute2.netlink import NLA_F_NESTED
from pyroute2.protocols import ETH_P_ALL
from common import stats2
from common import TCA_ACT_MAX_PRIO
from common_act import get_tca_action
from common_act import nla_plus_tca_act_opt
from act_police import nla_plus_police
from act_police import get_parameters as ap_parameters
from socket import htons

parent = TC_H_ROOT
TCA_BPF_FLAG_ACT_DIRECT = 1


def fix_msg(msg, kwarg):
    msg['info'] = htons(kwarg.pop('protocol', ETH_P_ALL) & 0xffff) |\
        ((kwarg.pop('prio', 0) << 16) & 0xffff0000)


def get_parameters(kwarg):
    ret = {'attrs': []}
    attrs_map = (
        # ('action', 'TCA_BPF_ACT'),
        # ('police', 'TCA_BPF_POLICE'),
        ('classid', 'TCA_BPF_CLASSID'),
        ('fd', 'TCA_BPF_FD'),
        ('name', 'TCA_BPF_NAME'),
        ('flags', 'TCA_BPF_FLAGS'),
    )

    act = kwarg.get('action')
    if act:
        ret['attrs'].append(['TCA_BPF_ACT', get_tca_action(kwarg)])

    if kwarg.get('rate'):
        ret['attrs'].append(['TCA_BPF_POLICE', ap_parameters(kwarg)])

    kwarg['flags'] = kwarg.get('flags', 0)
    if kwarg.get('direct_action', False):
        kwarg['flags'] |= TCA_BPF_FLAG_ACT_DIRECT

    for k, v in attrs_map:
        r = kwarg.get(k, None)
        if r is not None:
            ret['attrs'].append([v, r])

    return ret


class options(nla, nla_plus_police):
    nla_map = (('TCA_BPF_UNSPEC', 'none'),
               ('TCA_BPF_ACT', 'bpf_act'),
               ('TCA_BPF_POLICE', 'police'),
               ('TCA_BPF_CLASSID', 'uint32'),
               ('TCA_BPF_OPS_LEN', 'uint32'),
               ('TCA_BPF_OPS', 'uint32'),
               ('TCA_BPF_FD', 'uint32'),
               ('TCA_BPF_NAME', 'asciiz'),
               ('TCA_BPF_FLAGS', 'uint32'))

    class bpf_act(nla):
        nla_flags = NLA_F_NESTED
        nla_map = tuple([('TCA_ACT_PRIO_%i' % x, 'tca_act_bpf') for x
                         in range(TCA_ACT_MAX_PRIO)])

        class tca_act_bpf(nla,
                          nla_plus_tca_act_opt):
            nla_map = (('TCA_ACT_UNSPEC', 'none'),
                       ('TCA_ACT_KIND', 'asciiz'),
                       ('TCA_ACT_OPTIONS', 'get_act_options'),
                       ('TCA_ACT_INDEX', 'hex'),
                       ('TCA_ACT_STATS', 'get_stats2'))

            def get_stats2(self, *argv, **kwarg):
                return stats2
