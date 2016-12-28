import elasticsearch
import elasticsearch.client

from newrelic.hooks.datastore_elasticsearch import (
        _elasticsearch_client_methods,
        _elasticsearch_client_indices_methods,
        _elasticsearch_client_cat_methods,
        _elasticsearch_client_cluster_methods,
        _elasticsearch_client_nodes_methods,
        _elasticsearch_client_snapshot_methods,
        _elasticsearch_client_tasks_methods,
        _elasticsearch_client_ingest_methods,
)

def _test_methods_wrapped(object, method_name_tuples):
    for method_name, _ in method_name_tuples:
        method = getattr(object, method_name, None)
        if method is not None:
            err = '%s.%s isnt being wrapped' % (object, method)
            assert hasattr(method, '__wrapped__'), err

def test_instrumented_methods():
    _test_methods_wrapped(elasticsearch.Elasticsearch,
            _elasticsearch_client_methods)
    _test_methods_wrapped(elasticsearch.client.IndicesClient,
            _elasticsearch_client_indices_methods)
    _test_methods_wrapped(elasticsearch.client.ClusterClient,
            _elasticsearch_client_cluster_methods)

    if hasattr(elasticsearch.client, 'CatClient'):
        _test_methods_wrapped(elasticsearch.client.CatClient,
                _elasticsearch_client_cat_methods)

    if hasattr(elasticsearch.client, 'NodesClient'):
        _test_methods_wrapped(elasticsearch.client.NodesClient,
                _elasticsearch_client_nodes_methods)

    if hasattr(elasticsearch.client, 'SnapshotClient'):
        _test_methods_wrapped(elasticsearch.client.SnapshotClient,
                _elasticsearch_client_snapshot_methods)

    if hasattr(elasticsearch.client, 'TasksClient'):
        _test_methods_wrapped(elasticsearch.client.TasksClient,
                _elasticsearch_client_tasks_methods)

    if hasattr(elasticsearch.client, 'IngestClient'):
        _test_methods_wrapped(elasticsearch.client.IngestClient,
                _elasticsearch_client_ingest_methods)
