from __future__ import with_statement
  
import logging
import sys
import time
import unittest

import newrelic.tests.test_cases

import newrelic.api.settings
import newrelic.api.application
import newrelic.api.web_transaction
import newrelic.api.function_trace

settings = newrelic.api.settings.settings()
application = newrelic.api.application.application_instance()

@newrelic.api.function_trace.function_trace(name='_test_function_1')
def _test_function_1():
    time.sleep(1.0)

@newrelic.api.function_trace.function_trace()
def _test_function_nn_1():
    time.sleep(0.1)

class _test_class_nn_2:
    def _test_function(self):
        time.sleep(0.1)

_test_class_instance_nn_2 = _test_class_nn_2()
_test_class_instance_nn_2._test_function = \
        newrelic.api.function_trace.function_trace()(
        _test_class_instance_nn_2._test_function)

class _test_class_nn_3(object):
    def _test_function(self):
        time.sleep(0.1)

_test_class_instance_nn_3 = _test_class_nn_3()
_test_class_instance_nn_3._test_function = \
        newrelic.api.function_trace.function_trace()(
        _test_class_instance_nn_3._test_function)

class _test_class_nn_4:
    @newrelic.api.function_trace.function_trace()
    def _test_function(self):
        time.sleep(0.1)

_test_class_instance_nn_4 = _test_class_nn_4()

class _test_class_nn_5(object):
    @newrelic.api.function_trace.function_trace()
    def _test_function(self):
        time.sleep(0.1)

_test_class_instance_nn_5 = _test_class_nn_5()

def _test_function_6(name):
    time.sleep(0.1)
_test_function_6 = newrelic.api.function_trace.function_trace(
        lambda x: x)(_test_function_6)

class TestCase(newrelic.tests.test_cases.TestCase):

    requires_collector = True

    def test_function_trace(self):
        environ = { "REQUEST_URI": "/function_trace" }
        transaction = newrelic.api.web_transaction.WebTransaction(
              application, environ)
        with transaction:
            time.sleep(0.2)
            with newrelic.api.function_trace.FunctionTrace(
                    transaction, "function-1"):
                time.sleep(0.1)
                with newrelic.api.function_trace.FunctionTrace(
                        transaction, "function-1-1"):
                    time.sleep(0.1)
                with newrelic.api.function_trace.FunctionTrace(
                        transaction, "function-1-2"):
                    time.sleep(0.1)
                time.sleep(0.1)
            with newrelic.api.function_trace.FunctionTrace(
                    transaction, "function-2"):
                time.sleep(0.1)
                with newrelic.api.function_trace.FunctionTrace(
                        transaction, "function-2-1"):
                    time.sleep(0.1)
                    with newrelic.api.function_trace.FunctionTrace(
                            transaction, "function-2-1-1"):
                        time.sleep(0.1)
                    time.sleep(0.1)
                time.sleep(0.1)
            time.sleep(0.2)

    def test_transaction_not_running(self):
        environ = { "REQUEST_URI": "/transaction_not_running" }
        transaction = newrelic.api.web_transaction.WebTransaction(
                application, environ)
        try:
            with newrelic.api.function_trace.FunctionTrace(
                    transaction, "function"):
                time.sleep(0.1)
        except RuntimeError:
            pass

    def test_function_trace_decorator(self):
        environ = { "REQUEST_URI": "/function_trace_decorator" }
        transaction = newrelic.api.web_transaction.WebTransaction(
                application, environ)
        with transaction:
            time.sleep(0.1)
            _test_function_1()
            time.sleep(0.1)

    def test_function_trace_decorator_error(self):
        environ = { "REQUEST_URI": "/function_trace_decorator_error" }
        transaction = newrelic.api.web_transaction.WebTransaction(
                application, environ)
        with transaction:
            try:
                _test_function_1()
            except TypeError:
                pass

    def test_function_trace_decorator_no_name(self):
        environ = { "REQUEST_URI": "/function_trace_decorator_no_name" }
        transaction = newrelic.api.web_transaction.WebTransaction(
                application, environ)
        with transaction:
            time.sleep(0.1)
            _test_function_nn_1()
            _test_class_instance_nn_2._test_function()
            _test_class_instance_nn_3._test_function()
            _test_class_instance_nn_4._test_function()
            _test_class_instance_nn_5._test_function()
            _test_function_6("function+lambda")
            time.sleep(0.1)

if __name__ == '__main__':
    unittest.main()