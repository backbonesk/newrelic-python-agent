import MySQLdb

from testing_support.fixtures import (validate_transaction_metrics,
    validate_database_trace_inputs, override_application_settings)
from testing_support.settings import mysql_multiple_settings
from testing_support.util import instance_hostname

from newrelic.api.background_task import background_task

DB_MULTIPLE_SETTINGS = mysql_multiple_settings()
DB_SETTINGS = DB_MULTIPLE_SETTINGS[0]

# Settings

_enable_instance_settings = {
    'datastore_tracer.instance_reporting.enabled': True,
}
_disable_instance_settings = {
    'datastore_tracer.instance_reporting.enabled': False,
}

# Metrics

_base_scoped_metrics = (
        ('Function/MySQLdb:Connect', 1),
        ('Function/MySQLdb.connections:Connection.__enter__', 1),
        ('Function/MySQLdb.connections:Connection.__exit__', 1),
        ('Datastore/operation/MySQL/rollback', 1),
)

_base_rollup_metrics = (
        ('Datastore/all', 2),
        ('Datastore/allOther', 2),
        ('Datastore/MySQL/all', 2),
        ('Datastore/MySQL/allOther', 2),
        ('Datastore/operation/MySQL/rollback', 1),
)

_disable_scoped_metrics = list(_base_scoped_metrics)
_disable_rollup_metrics = list(_base_rollup_metrics)

_enable_scoped_metrics = list(_base_scoped_metrics)
_enable_rollup_metrics = list(_base_rollup_metrics)

_host = instance_hostname(DB_SETTINGS['host'])
_port = DB_SETTINGS['port']

_instance_metric_name = 'Datastore/instance/MySQL/%s/%s' % (_host, _port)

_enable_rollup_metrics.append(
        (_instance_metric_name, 1)
)

_disable_rollup_metrics.append(
        (_instance_metric_name, None)
)

# Tests

@override_application_settings(_enable_instance_settings)
@validate_transaction_metrics('test_rollback:test_rollback_on_exception_enable',
        scoped_metrics=_enable_scoped_metrics,
        rollup_metrics=_enable_rollup_metrics,
        background_task=True)
@validate_database_trace_inputs(sql_parameters_type=tuple)
@background_task()
def test_rollback_on_exception_enable():
    try:
        with MySQLdb.connect(
            db=DB_SETTINGS['name'], user=DB_SETTINGS['user'],
            passwd=DB_SETTINGS['password'], host=DB_SETTINGS['host'],
            port=DB_SETTINGS['port']):

            raise RuntimeError('error')
    except RuntimeError:
        pass

@override_application_settings(_disable_instance_settings)
@validate_transaction_metrics('test_rollback:test_rollback_on_exception_disable',
        scoped_metrics=_disable_scoped_metrics,
        rollup_metrics=_disable_rollup_metrics,
        background_task=True)
@validate_database_trace_inputs(sql_parameters_type=tuple)
@background_task()
def test_rollback_on_exception_disable():
    try:
        with MySQLdb.connect(
            db=DB_SETTINGS['name'], user=DB_SETTINGS['user'],
            passwd=DB_SETTINGS['password'], host=DB_SETTINGS['host'],
            port=DB_SETTINGS['port']):

            raise RuntimeError('error')
    except RuntimeError:
        pass