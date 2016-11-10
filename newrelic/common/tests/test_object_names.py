import datetime
import functools
import pytest
import sys
import unittest

from collections import namedtuple

import newrelic.packages.six as six
from newrelic.packages.six.moves import builtins

from newrelic.common.object_names import (callable_name,
        expand_builtin_exception_name)

def _function1(self): pass

def _function_a(a): pass

_partial_function1 = functools.partial(_function_a, a=1)

class _class1():

    def _function1(self): pass

    @classmethod
    def _function2(cls): pass

    @staticmethod
    def _function3(): pass

class _class2(object):

    def _function1(self): pass

    @classmethod
    def _function2(cls): pass

    @staticmethod
    def _function3(): pass

_class3 = namedtuple('_class3', 'a')

def _decorator1(wrapped):
    @functools.wraps(wrapped)
    def wrapper(*args, **kwargs):
        return wrapped(*args, **kwargs)
    return wrapper

class _decorator2(object):

    def __init__(self, wrapped):
        self._nr_wrapped = wrapped

        try:
            object.__setattr__(self, '__qualname__', wrapped.__qualname__)
        except AttributeError:
            pass

        try:
            object.__setattr__(self, '__name__', wrapped.__name__)
        except AttributeError:
            pass

    @property
    def __module__(self):
        return self._self_wrapped.__module__

    def __getattr__(self, name):
        return getattr(self._nr_wrapped, name)

    def __get__(self, instance, owner):
        descriptor = self._nr_wrapped.__get__(instance, owner)
        return self.__class__(descriptor)

    def __call__(self, *args, **kwargs):
        return self._nr_wrapped(*args, **kwargs)

    def decorator(self, *args, **kwargs):
        pass

@_decorator1
def _function2(self): pass

@_decorator2
def _function3(self): pass

class _class4(object):

    @_decorator1
    def _function1(self): pass

    @_decorator2
    def _function2(self): pass

class _class5(object):
    class _class6(object):
        def _function1(self): pass

class _class7(_class1):
    def _function4(self): pass

class _class8(_class2):
    def _function4(self): pass

def _module_fqdn(path, name=None):
  name = name or __name__
  return '%s:%s' % (name, path)

class TestCallableName(unittest.TestCase):

    def test_function_name(self):
        self.assertEqual(callable_name(_function1),
                _module_fqdn('_function1'))

    def test_function_partial(self):
        self.assertEqual(callable_name(_partial_function1),
                _module_fqdn('_function_a'))

    def test_old_class_type(self):
        self.assertEqual(callable_name(_class1),
                _module_fqdn('_class1'))

    def test_old_class_instance(self):
        self.assertEqual(callable_name(_class1()),
                _module_fqdn('_class1'))

    def test_old_class_type_instancemethod(self):
        self.assertEqual(callable_name(_class1._function1),
                _module_fqdn('_class1._function1'))

    def test_old_class_instance_instancemethod(self):
        self.assertEqual(callable_name(_class1()._function1),
                _module_fqdn('_class1._function1'))

    def test_old_class_type_classmethod(self):
        self.assertEqual(callable_name(_class1._function2),
                _module_fqdn('_class1._function2'))

    def test_old_class_instance_classmethod(self):
        self.assertEqual(callable_name(_class1()._function2),
                _module_fqdn('_class1._function2'))

    def test_old_class_type_staticmethod(self):
        if six.PY3:
            self.assertEqual(callable_name(_class1._function3),
                    _module_fqdn('_class1._function3'))
        else:
            # Cannot work out class name for Python 2.
            self.assertEqual(callable_name(_class1._function3),
                    _module_fqdn('_function3'))

    def test_old_class_instance_staticmethod(self):
        if six.PY3:
            self.assertEqual(callable_name(_class1._function3),
                    _module_fqdn('_class1._function3'))
        else:
            # Cannot work out class name for Python 2.
            self.assertEqual(callable_name(_class1._function3),
                    _module_fqdn('_function3'))

    def test_new_class_type(self):
        self.assertEqual(callable_name(_class2),
                _module_fqdn('_class2'))

    def test_new_class_instance(self):
        self.assertEqual(callable_name(_class2()),
                _module_fqdn('_class2'))

    def test_new_class_type_instancemethod(self):
        self.assertEqual(callable_name(_class2._function1),
                _module_fqdn('_class2._function1'))

    def test_new_class_instance_instancemethod(self):
        self.assertEqual(callable_name(_class2()._function1),
                _module_fqdn('_class2._function1'))

    def test_new_class_type_classmethod(self):
        self.assertEqual(callable_name(_class2._function2),
                _module_fqdn('_class2._function2'))

    def test_new_class_instance_classmethod(self):
        self.assertEqual(callable_name(_class2()._function2),
                _module_fqdn('_class2._function2'))

    def test_new_class_type_staticmethod(self):
        if six.PY3:
            self.assertEqual(callable_name(_class2._function3),
                    _module_fqdn('_class2._function3'))
        else:
            # Cannot work out class name for Python 2.
            self.assertEqual(callable_name(_class2._function3),
                    _module_fqdn('_function3'))

    def test_new_class_instance_staticmethod(self):
        if six.PY3:
            self.assertEqual(callable_name(_class2._function3),
                    _module_fqdn('_class2._function3'))
        else:
            # Cannot work out class name for Python 2.
            self.assertEqual(callable_name(_class2._function3),
                    _module_fqdn('_function3'))

    def test_generated_class_type(self):
        self.assertEqual(callable_name(_class3),
                _module_fqdn('_class3'))

    def test_generated_class_instance(self):
        self.assertEqual(callable_name(_class3(1)),
                _module_fqdn('_class3'))

    def test_generated_class_type_instancemethod(self):
        # Cannot work out module name of method bound class for
        # Python 3. Make consistent between 2 and use Python 3.
        self.assertEqual(callable_name(_class3._asdict),
                _module_fqdn('_class3._asdict', '<namedtuple__class3>'))

    def test_generated_class_instance_instancemethod(self):
        if six.PY3:
            self.assertEqual(callable_name(_class3(1)._asdict),
                    _module_fqdn('_class3._asdict', '<namedtuple__class3>'))
        else:
            self.assertEqual(callable_name(_class3(1)._asdict),
                    _module_fqdn('_class3._asdict'))

    def test_generated_class_type_staticmethod(self):
        if six.PY3:
            self.assertEqual(callable_name(_class3._make),
                    _module_fqdn('_class3._make', '<namedtuple__class3>'))
        else:
            self.assertEqual(callable_name(_class3._make),
                    _module_fqdn('_class3._make'))

    def test_generated_class_instance_staticmethod(self):
        if six.PY3:
            self.assertEqual(callable_name(_class3(1)._make),
                    _module_fqdn('_class3._make', '<namedtuple__class3>'))
        else:
            self.assertEqual(callable_name(_class3(1)._make),
                    _module_fqdn('_class3._make'))

    def test_function_name_wraps_decorator(self):
        self.assertEqual(callable_name(_function2),
                _module_fqdn('_function2'))

    def test_function_name_desc_decorator(self):
        self.assertEqual(callable_name(_function3),
                _module_fqdn('_function3'))

    def test_new_class_type_instancemethod_wraps_decorator(self):
        self.assertEqual(callable_name(_class4._function1),
                _module_fqdn('_class4._function1'))

    def test_new_class_instance_instancemethod_wraps_decorator(self):
        self.assertEqual(callable_name(_class4()._function1),
                _module_fqdn('_class4._function1'))

    def test_new_class_type_instancemethod_desc_decorator(self):
        if six.PY3:
            self.assertEqual(callable_name(_class4._function2),
                    _module_fqdn('_class4._function2'))
        else:
            # Cannot work out class name for Python 2.
            self.assertEqual(callable_name(_class4._function2),
                    _module_fqdn('_function2'))

    def test_new_class_instance_instancemethod_desc_decorator(self):
        if six.PY3:
            self.assertEqual(callable_name(_class4()._function2),
                    _module_fqdn('_class4._function2'))
        else:
            # Cannot work out class name for Python 2.
            self.assertEqual(callable_name(_class4()._function2),
                    _module_fqdn('_function2'))

    def test_builtin_function_name(self):
        self.assertEqual(callable_name(globals),
                _module_fqdn('globals', builtins.__name__))

    def test_builtin_class_type(self):
        self.assertEqual(callable_name(list),
                _module_fqdn('list', builtins.__name__))

    def test_builtin_class_instance(self):
        self.assertEqual(callable_name(list()),
                _module_fqdn('list', builtins.__name__))

    def test_builtin_class_type_methoddescriptor(self):
        self.assertEqual(callable_name(list.pop),
                _module_fqdn('list.pop', builtins.__name__))

    def test_builtin_class_instance_methoddescriptor(self):
        self.assertEqual(callable_name(list().pop),
                _module_fqdn('list.pop', builtins.__name__))

    def test_builtin_class_type_slotwrapper(self):
        self.assertEqual(callable_name(int.__add__),
                _module_fqdn('int.__add__', builtins.__name__))

    def test_builtin_class_instance_slotwrapper(self):
        self.assertEqual(callable_name(int().__add__),
                _module_fqdn('int.__add__', builtins.__name__))

    def test_nested_class_type(self):
        if six.PY3:
            self.assertEqual(callable_name(_class5._class6),
                    _module_fqdn('_class5._class6'))
        else:
            # Cannot work out nested contexts for Python 2.
            self.assertEqual(callable_name(_class5._class6),
                    _module_fqdn('_class6'))

    def test_nested_class_instance(self):
        if six.PY3:
            self.assertEqual(callable_name(_class5._class6()),
                    _module_fqdn('_class5._class6'))
        else:
            # Cannot work out nested contexts for Python 2.
            self.assertEqual(callable_name(_class5._class6()),
                    _module_fqdn('_class6'))

    def test_nested_class_type_instancemethod(self):
        if six.PY3:
            self.assertEqual(callable_name(_class5._class6._function1),
                    _module_fqdn('_class5._class6._function1'))
        else:
            # Cannot work out nested contexts for Python 2.
            self.assertEqual(callable_name(_class5._class6._function1),
                    _module_fqdn('_class6._function1'))

    def test_nested_class_instance_instancemethod(self):
        if six.PY3:
            self.assertEqual(callable_name(_class5._class6()._function1),
                    _module_fqdn('_class5._class6._function1'))
        else:
            # Cannot work out nested contexts for Python 2.
            self.assertEqual(callable_name(_class5._class6()._function1),
                    _module_fqdn('_class6._function1'))

    def test_extension_class_type(self):
        self.assertEqual(callable_name(datetime.date),
                _module_fqdn('date', 'datetime'))

    def test_extension_method_via_class(self):
        self.assertEqual(callable_name(datetime.date.strftime),
                _module_fqdn('date.strftime', 'datetime'))

    def test_extension_method_via_instance(self):
        self.assertEqual(callable_name(datetime.date(200, 1, 1).strftime),
                _module_fqdn('date.strftime', 'datetime'))

    @pytest.mark.skipif(six.PY3,
            reason='Yet to be able to work out name of subclass')
    def test_subclass_old_class_type_instancemethod(self):
        self.assertEqual(callable_name(_class7._function1),
                _module_fqdn('_class7._function1'))

    @pytest.mark.skipif(six.PY3,
            reason='Yet to be able to work out name of subclass')
    def test_subclass_old_class_instance_instancemethod(self):
        self.assertEqual(callable_name(_class7()._function1),
                _module_fqdn('_class7._function1'))

    def test_subclass_old_class_type_classmethod(self):
        self.assertEqual(callable_name(_class7._function2),
                _module_fqdn('_class7._function2'))

    def test_subclass_old_class_instance_classmethod(self):
        self.assertEqual(callable_name(_class7()._function2),
                _module_fqdn('_class7._function2'))

    @pytest.mark.skipif(six.PY3,
            reason='Yet to be able to work out name of subclass')
    def test_subclass_old_class_type_staticmethod(self):
        if six.PY3:
            self.assertEqual(callable_name(_class7._function3),
                    _module_fqdn('_class7._function3'))
        else:
            # Cannot work out class name for Python 2.
            self.assertEqual(callable_name(_class7._function3),
                    _module_fqdn('_function3'))

    @pytest.mark.skipif(six.PY3,
            reason='Yet to be able to work out name of subclass')
    def test_subclass_old_class_instance_staticmethod(self):
        if six.PY3:
            self.assertEqual(callable_name(_class7()._function3),
                    _module_fqdn('_class7._function3'))
        else:
            # Cannot work out class name for Python 2.
            self.assertEqual(callable_name(_class7()._function3),
                    _module_fqdn('_function3'))

    def test_subclass_old_class_non_inherited_method(self):
        self.assertEqual(callable_name(_class7()._function4),
                _module_fqdn('_class7._function4'))

    @pytest.mark.skipif(six.PY3,
            reason='Yet to be able to work out name of subclass')
    def test_subclass_new_class_type_instancemethod(self):
        self.assertEqual(callable_name(_class8._function1),
                _module_fqdn('_class8._function1'))

    @pytest.mark.skipif(six.PY3,
            reason='Yet to be able to work out name of subclass')
    def test_subclass_new_class_instance_instancemethod(self):
        self.assertEqual(callable_name(_class8()._function1),
                _module_fqdn('_class8._function1'))

    def test_subclass_new_class_type_classmethod(self):
        self.assertEqual(callable_name(_class8._function2),
                _module_fqdn('_class8._function2'))

    def test_subclass_new_class_instance_classmethod(self):
        self.assertEqual(callable_name(_class8()._function2),
                _module_fqdn('_class8._function2'))

    @pytest.mark.skipif(six.PY3,
            reason='Yet to be able to work out name of subclass')
    def test_subclass_new_class_type_staticmethod(self):
        if six.PY3:
            self.assertEqual(callable_name(_class8._function3),
                    _module_fqdn('_class8._function3'))
        else:
            # Cannot work out class name for Python 2.
            self.assertEqual(callable_name(_class8._function3),
                    _module_fqdn('_function3'))

    @pytest.mark.skipif(six.PY3,
            reason='Yet to be able to work out name of subclass')
    def test_subclass_new_class_instance_staticmethod(self):
        if six.PY3:
            self.assertEqual(callable_name(_class8()._function3),
                    _module_fqdn('_class8._function3'))
        else:
            # Cannot work out class name for Python 2.
            self.assertEqual(callable_name(_class8()._function3),
                    _module_fqdn('_function3'))

    def test_subclass_new_class_non_inherited_method(self):
        self.assertEqual(callable_name(_class8()._function4),
                _module_fqdn('_class8._function4'))

class TestExpandBuiltinExceptionName(unittest.TestCase):

    def test_builtin_exception(self):
        result = expand_builtin_exception_name('KeyError')
        if six.PY3:
            self.assertEqual(result, 'builtins:KeyError')
        elif six.PY2:
            self.assertEqual(result, 'exceptions:KeyError')
        else:
            self.assertEqual(result, 'KeyError')

    def test_base_exception(self):
        result = expand_builtin_exception_name('BaseException')
        if six.PY3:
            self.assertEqual(result, 'builtins:BaseException')
        elif six.PY2:
            self.assertEqual(result, 'exceptions:BaseException')
        else:
            self.assertEqual(result, 'BaseException')

    def test_warning(self):
        result = expand_builtin_exception_name('UnicodeWarning')
        if six.PY3:
            self.assertEqual(result, 'builtins:UnicodeWarning')
        elif six.PY2:
            self.assertEqual(result, 'exceptions:UnicodeWarning')
        else:
            self.assertEqual(result, 'UnicodeWarning')

    def test_py3_exception_only(self):
        result = expand_builtin_exception_name('BrokenPipeError')
        if six.PY3:
            self.assertEqual(result, 'builtins:BrokenPipeError')
        else:
            self.assertEqual(result, 'BrokenPipeError')

    def test_not_builtin(self):
        result = expand_builtin_exception_name('Foo')
        self.assertEqual(result, 'Foo')

    def test_builtin_not_exception(self):
        result = expand_builtin_exception_name('sum')
        self.assertEqual(result, 'sum')

    def test_not_builtin_with_colon(self):
        result = expand_builtin_exception_name('MyModule:KeyError')
        self.assertEqual(result, 'MyModule:KeyError')

if __name__ == '__main__':
    unittest.main()
