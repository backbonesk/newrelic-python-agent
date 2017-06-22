import pika
import six

from newrelic.api.background_task import background_task
from newrelic.api.transaction import end_of_transaction

from conftest import QUEUE, EXCHANGE, BODY
from testing_support.fixtures import (capture_transaction_metrics,
        validate_transaction_metrics)
from testing_support.settings import rabbitmq_settings

DB_SETTINGS = rabbitmq_settings()


_test_blocking_connection_basic_get_metrics = [
    ('MessageBroker/RabbitMQ/Exchange/Produce/Named/%s' % EXCHANGE, None),
    ('MessageBroker/RabbitMQ/Exchange/Consume/Named/%s' % EXCHANGE, 1),
    (('Function/pika.adapters.blocking_connection:'
            '_CallbackResult.set_value_once'), 1)
]


@validate_transaction_metrics(
        ('test_pika_blocking_connection_consume:'
                'test_blocking_connection_basic_get'),
        scoped_metrics=_test_blocking_connection_basic_get_metrics,
        rollup_metrics=_test_blocking_connection_basic_get_metrics,
        background_task=True)
@background_task()
def test_blocking_connection_basic_get(producer):
    with pika.BlockingConnection(
            pika.ConnectionParameters(DB_SETTINGS['host'])) as connection:
        channel = connection.channel()
        method_frame, _, _ = channel.basic_get(QUEUE)
        assert method_frame
        channel.basic_ack(method_frame.delivery_tag)


_test_blocking_connection_basic_get_empty_metrics = [
    ('MessageBroker/RabbitMQ/Exchange/Produce/Named/%s' % EXCHANGE, None),
    ('MessageBroker/RabbitMQ/Exchange/Consume/Named/%s' % EXCHANGE, None),
]


@validate_transaction_metrics(
        ('test_pika_blocking_connection_consume:'
                'test_blocking_connection_basic_get_empty'),
        scoped_metrics=_test_blocking_connection_basic_get_empty_metrics,
        rollup_metrics=_test_blocking_connection_basic_get_empty_metrics,
        background_task=True)
@background_task()
def test_blocking_connection_basic_get_empty():
    QUEUE = 'test_blocking_empty'

    with pika.BlockingConnection(
            pika.ConnectionParameters(DB_SETTINGS['host'])) as connection:
        channel = connection.channel()
        channel.queue_declare(queue=QUEUE)

        try:
            method_frame, _, _ = channel.basic_get(QUEUE)
            assert method_frame is None
        finally:
            channel.queue_delete(queue=QUEUE)


def test_blocking_connection_basic_get_outside_transaction(producer):
    metrics_list = []

    @capture_transaction_metrics(metrics_list)
    def test_basic_get():
        with pika.BlockingConnection(
                pika.ConnectionParameters(DB_SETTINGS['host'])) as connection:
            channel = connection.channel()
            channel.queue_declare(queue=QUEUE)

            method_frame, _, _ = channel.basic_get(QUEUE)
            channel.basic_ack(method_frame.delivery_tag)
            assert method_frame

    test_basic_get()

    # Confirm that no metrics have been created. This is because no background
    # task should be created for basic_get actions.
    assert not metrics_list


_test_blocking_conn_basic_consume_no_txn_metrics = [
    ('MessageBroker/RabbitMQ/Exchange/Produce/Named/%s' % EXCHANGE, None),
    ('MessageBroker/RabbitMQ/Exchange/Consume/Named/%s' % EXCHANGE, 1),
]

if six.PY3:
    _test_blocking_conn_basic_consume_no_txn_metrics.append(
        (('Function/test_pika_blocking_connection_consume:'
          'test_blocking_connection_basic_consume_outside_transaction.'
          '<locals>.on_message'), 1))
else:
    _test_blocking_conn_basic_consume_no_txn_metrics.append(
        ('Function/test_pika_blocking_connection_consume:on_message', 1))


@validate_transaction_metrics(
        'Named/%s' % EXCHANGE,
        scoped_metrics=_test_blocking_conn_basic_consume_no_txn_metrics,
        rollup_metrics=_test_blocking_conn_basic_consume_no_txn_metrics,
        background_task=True,
        group='Message/RabbitMQ/Exchange')
def test_blocking_connection_basic_consume_outside_transaction(producer):
    def on_message(channel, method_frame, header_frame, body):
        assert hasattr(method_frame, '_nr_start_time')
        assert body == BODY
        channel.stop_consuming()

    with pika.BlockingConnection(
            pika.ConnectionParameters(DB_SETTINGS['host'])) as connection:
        channel = connection.channel()
        channel.basic_consume(on_message, QUEUE)
        try:
            channel.start_consuming()
        except:
            channel.stop_consuming()
            raise


_test_blocking_conn_basic_consume_in_txn_metrics = [
    ('MessageBroker/RabbitMQ/Exchange/Produce/Named/%s' % EXCHANGE, None),
    ('MessageBroker/RabbitMQ/Exchange/Consume/Named/%s' % EXCHANGE, 1),
]

if six.PY3:
    _test_blocking_conn_basic_consume_in_txn_metrics.append(
        (('Function/test_pika_blocking_connection_consume:'
          'test_blocking_connection_basic_consume_inside_txn.'
          '<locals>.on_message'), 1))
else:
    _test_blocking_conn_basic_consume_in_txn_metrics.append(
        ('Function/test_pika_blocking_connection_consume:on_message', 1))


@validate_transaction_metrics(
        ('test_pika_blocking_connection_consume:'
                'test_blocking_connection_basic_consume_inside_txn'),
        scoped_metrics=_test_blocking_conn_basic_consume_in_txn_metrics,
        rollup_metrics=_test_blocking_conn_basic_consume_in_txn_metrics,
        background_task=True)
@background_task()
def test_blocking_connection_basic_consume_inside_txn(producer):
    def on_message(channel, method_frame, header_frame, body):
        assert hasattr(method_frame, '_nr_start_time')
        assert body == BODY
        channel.stop_consuming()

    with pika.BlockingConnection(
            pika.ConnectionParameters(DB_SETTINGS['host'])) as connection:
        channel = connection.channel()
        channel.basic_consume(on_message, QUEUE)
        try:
            channel.start_consuming()
        except:
            channel.stop_consuming()
            raise


_test_blocking_conn_basic_consume_stopped_txn_metrics = [
    ('MessageBroker/RabbitMQ/Exchange/Produce/Named/%s' % EXCHANGE, None),
    ('MessageBroker/RabbitMQ/Exchange/Consume/Named/%s' % EXCHANGE, None),
]

if six.PY3:
    _test_blocking_conn_basic_consume_stopped_txn_metrics.append(
        (('Function/test_pika_blocking_connection_consume:'
          'test_blocking_connection_basic_consume_stopped_txn.'
          '<locals>.on_message'), None))
else:
    _test_blocking_conn_basic_consume_stopped_txn_metrics.append(
        ('Function/test_pika_blocking_connection_consume:on_message', None))


@validate_transaction_metrics(
        ('test_pika_blocking_connection_consume:'
                'test_blocking_connection_basic_consume_stopped_txn'),
        scoped_metrics=_test_blocking_conn_basic_consume_stopped_txn_metrics,
        rollup_metrics=_test_blocking_conn_basic_consume_stopped_txn_metrics,
        background_task=True)
@background_task()
def test_blocking_connection_basic_consume_stopped_txn(producer):
    def on_message(channel, method_frame, header_frame, body):
        assert hasattr(method_frame, '_nr_start_time')
        assert body == BODY
        channel.stop_consuming()

    end_of_transaction()

    with pika.BlockingConnection(
            pika.ConnectionParameters(DB_SETTINGS['host'])) as connection:
        channel = connection.channel()
        channel.basic_consume(on_message, QUEUE)
        try:
            channel.start_consuming()
        except:
            channel.stop_consuming()
            raise


_test_blocking_connection_consume_metrics = [
    ('MessageBroker/RabbitMQ/Exchange/Produce/Named/%s' % EXCHANGE, None),
    # TODO: This test needs to be re-enabled (count=1) with PYTHON-2364
    ('MessageBroker/RabbitMQ/Exchange/Consume/Named/%s' % EXCHANGE, None),
]


@validate_transaction_metrics(
        ('test_pika_blocking_connection_consume:'
                'test_blocking_connection_consume'),
        scoped_metrics=_test_blocking_connection_consume_metrics,
        rollup_metrics=_test_blocking_connection_consume_metrics,
        background_task=True)
@background_task()
def test_blocking_connection_consume(producer):
    with pika.BlockingConnection(
            pika.ConnectionParameters(DB_SETTINGS['host'])) as connection:
        channel = connection.channel()
        for method_frame, properties, body in channel.consume(QUEUE):
            assert hasattr(method_frame, '_nr_start_time')
            assert body == BODY
            break
