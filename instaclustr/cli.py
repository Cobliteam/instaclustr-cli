import argparse
import logging
import os
import sys
import time

from instaclustr.api import InstaclustrProvisioning, InstaclustrMonitoring


class MonitoringCommands(object):
    def __init__(self, args):
        self.api = InstaclustrMonitoring(args.username,
                                         args.monitoring_api_key)
        self.out = sys.stdout

    def wait_for_pending_compactions(self, check_interval, cluster_id=None,
                                     datacenter_id=None,
                                     node_id=None, **kwargs):
        while True:
            metrics_data = self.api.get_metrics(
                ['n::compactions'], '1m', cluster_id=cluster_id,
                datacenter_id=datacenter_id, node_id=node_id)
            all_nodes = set(node_data['id'] for node_data in metrics_data)
            nodes_ok = set()
            for node_data in metrics_data:
                _, compactions = next(
                    InstaclustrMonitoring.extract_metric_values(
                        node_data, 'compactions', 'pendingtasks'))
                if compactions < 1:
                    nodes_ok.add(node_data['id'])

            nodes_not_ok = all_nodes.difference(nodes_ok)
            if nodes_not_ok:
                logging.info('Nodes are still doing compactions, waiting: %s',
                             ', '.join(nodes_not_ok))
                time.sleep(check_interval)
            else:
                break


class ProvisioningCommands(object):
    def __init__(self, args):
        self.api = InstaclustrProvisioning(args.username,
                                           args.provisioning_api_key)
        self.out = sys.stdout

    def get_cluster_contact_points(self, cluster_id, datacenter=None,
                                   private=False, **kwargs):
        cluster_info = self.api.get_cluster(cluster_id)
        node_addrs = set()

        for dc_info in cluster_info['dataCentres']:
            if datacenter and dc_info['name'] != datacenter:
                continue

            for node_info in dc_info['nodes']:
                addr = (node_info['privateAddress'] if private
                        else node_info['publicAddress'])
                node_addrs.add(addr)

        for addr in node_addrs:
            self.out.write('{}\n'.format(addr))

        self.out.flush()


def add_cluster_id_arg(parser, **kwargs):
    return parser.add_argument(
        '--cluster-id', help='Cluster ID to target with commands', **kwargs)


def add_datacenter_id_arg(parser, **kwargs):
    return parser.add_argument(
        '--datacenter-id', help='Datacenter ID to target with commands',
        **kwargs)


def add_node_id_arg(parser, **kwargs):
    return parser.add_argument(
        '--node-id', help='Node ID to target with commands', **kwargs)


def add_node_selector_args(parser):
    group = parser.add_mutually_exclusive_group(required=True)
    add_cluster_id_arg(group)
    add_datacenter_id_arg(group)
    add_node_id_arg(group)
    return group


def main():
    logging.basicConfig(level=logging.INFO)

    argp = argparse.ArgumentParser(description='Instaclustr CLI utils')

    argp.add_argument(
        '--username',
        help='Instaclustr Username')
    argp.set_defaults(username=os.environ.get('INSTACLUSTR_USERNAME'))

    # Set up main command categories: monitoring, provisioning

    categories = argp.add_subparsers(dest='category')
    categories.required = True

    monitoring = categories.add_parser(
        'monitoring',
        help='Monitoring commands')
    monitoring.set_defaults(command_class=MonitoringCommands)

    provisioning = categories.add_parser(
        'provisioning',
        help='Provisioning commands')
    provisioning.set_defaults(command_class=ProvisioningCommands)

    # Set up monitoring commands

    monitoring.add_argument(
        '--monitoring-api-key',
        help='Instaclustr Monitoring API Key')
    monitoring.set_defaults(
        monitoring_api_key=os.environ.get('INSTACLUSTR_MONITORING_API_KEY'))

    monitoring_cmds = monitoring.add_subparsers(dest='action')
    monitoring_cmds.required = True

    wait_for_pending_compactions = monitoring_cmds.add_parser(
        'wait-for-pending-compactions',
        help='Wait until pending compactions have settled')
    wait_for_pending_compactions.add_argument(
        '--check-interval', type=float, default=60.0, metavar='SECONDS',
        help='How long to wait between metrics checks')
    add_node_selector_args(wait_for_pending_compactions)

    # Set up provisioning commands

    provisioning.add_argument(
        '--provisioning-api-key',
        help='Instaclustr Provisioning API Key')
    provisioning.set_defaults(
        provisioning_api_key=os.environ.get(
            'INSTACLUSTR_PROVISIONING_API_KEY'))

    provisioning_cmds = provisioning.add_subparsers(dest='action')
    provisioning_cmds.required = True

    get_cluster_contact_points = provisioning_cmds.add_parser(
        'get-cluster-contact-points',
        help='Get list of contact points for a cluster')
    get_cluster_contact_points.add_argument(
        '--datacenter',
        help='Restrict contact points to this datacenter')
    get_cluster_contact_points.add_argument(
        '--private', action='store_true',
        help='Retrieve private node address instead of public')
    add_cluster_id_arg(get_cluster_contact_points, required=True)

    # Run it

    args = argp.parse_args()
    command_instance = args.command_class(args)
    command_func = getattr(command_instance, args.action.replace('-', '_'))
    command_func(**vars(args))
