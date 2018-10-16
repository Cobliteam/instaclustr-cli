import json
from uuid import UUID

import iso8601
import requests
from urllib.parse import urljoin


class InstaclustrApi(requests.Session):
    DEFAULT_API_ENDPOINT: str = NotImplemented

    def __init__(self, username, api_key, api_endpoint=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.auth = (username, api_key)
        self.endpoint = api_endpoint or self.DEFAULT_API_ENDPOINT

    def request(self, method, url, *args, **kwargs):
        url = urljoin(self.endpoint, url)
        return super().request(method, url, *args, **kwargs)


class InstaclustrMonitoring(InstaclustrApi):
    DEFAULT_API_ENDPOINT = 'https://api.instaclustr.com/monitoring/v1/'

    @classmethod
    def extract_metric_values(cls, node_data, name, tpe):
        for metric_payload in node_data['payload']:
            if metric_payload['metric'] == name \
                    and metric_payload['type'] == tpe:
                for value_data in metric_payload['values']:
                    yield (iso8601.parse_date(value_data['time']),
                           float(value_data['value']))

    def get_metrics(self, metrics, period, report_nan=False, cluster_id=None,
                    datacenter_id=None,
                    node_id=None):
        if node_id:
            metrics_class = 'nodes'
            entity_id = node_id
        elif datacenter_id:
            metrics_class = 'datacenters'
            entity_id = datacenter_id
        elif cluster_id:
            metrics_class = 'clusters'
            entity_id = cluster_id
        else:
            raise ValueError('One of cluster_id, datacenter_id or node_id '
                             'must be specified')

        if not isinstance(metrics, str):
            metrics = ','.join(metrics)

        response = self.get(
            '{}/{}'.format(metrics_class, entity_id),
            params={'metrics': metrics, 'period': period,
                    'reportNaN': json.dumps(report_nan)})
        response.raise_for_status()

        return response.json()


class InstaclustrProvisioning(InstaclustrApi):
    DEFAULT_API_ENDPOINT = 'https://api.instaclustr.com/provisioning/v1/'

    def get_cluster(self, cluster_id):
        cluster_uuid = UUID(cluster_id)
        response = self.get(str(cluster_uuid))
        response.raise_for_status()

        return response.json()
