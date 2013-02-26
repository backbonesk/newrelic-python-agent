"""This module provides functions to collect information about the operating
system, Python and hosting environment.

"""

import newrelic

import sys
import os
import platform
import re

try:
    import multiprocessing
except:
    pass

try:
    import pkg_resources
except:
    pass

try:
    import newrelic.core._thread_utilization
except:
    pass

try:
    import newrelic.lib.simplejson._speedups
except:
    pass

_current_cpu_count = None

def cpu_count(update=False):
    """Return the number of processors host hardware provides.

    """

    global _current_cpu_count

    if not update and _current_cpu_count:
        return _current_cpu_count

    # TODO For more methods of determining this if required see
    # http://stackoverflow.com/questions/1006289.

    # Python 2.6+.

    if 'multiprocessing' in sys.modules:
        try:
            _current_cpu_count = multiprocessing.cpu_count()
            return _current_cpu_count
        except NotImplementedError:
            pass

    # POSIX Systems.

    try:
        res = os.sysconf('SC_NPROCESSORS_ONLN')
        if res > 0:
            _current_cpu_count = res
            return _current_cpu_count
    except (ValueError, OSError, AttributeError):
        pass

    # Fallback to indicating only a single processor.

    _current_cpu_count = 1

    return _current_cpu_count

def _get_available_memory():
    if sys.platform == 'linux2':
        try:
            parser = re.compile(r'^(?P<key>\S*):\s*(?P<value>\d*)\s*kB')

            fp = None

            try:
                fp = open('/proc/meminfo')

                for line in fp.readlines():
                    match = parser.match(line)
                    if not match:
                        continue
                    key, value = match.groups(['key', 'value'])
                    if key == 'MemTotal':
                        memory_bytes = float(value) * 1024
                        return memory_bytes / (1024*1024)

            except:
                pass

            finally:
                if fp:
                    fp.close()

        except IOError:
            return 0

    return 0

def environment_settings():
    """Returns an array of arrays of environment settings

    """

    env = []

    # Agent information.

    env.append(('Agent Version', '.'.join(map(str, newrelic.version_info))))

    if 'NEW_RELIC_ADMIN_COMMAND' in os.environ:
        env.append(('Admin Command', os.environ['NEW_RELIC_ADMIN_COMMAND']))
        del os.environ['NEW_RELIC_ADMIN_COMMAND']

    # System information.

    env.append(('Arch', platform.machine()))
    env.append(('OS', platform.system()))
    env.append(('OS version', platform.release()))
    env.append(('CPU Count', cpu_count()))
    env.append(('System Memory', _get_available_memory()))

    # Python information.

    env.append(('Python Program Name', sys.argv[0]))

    env.append(('Python Executable', sys.executable))

    env.append(('Python Home', os.environ.get('PYTHONHOME', '')))
    env.append(('Python Path', os.environ.get('PYTHONPATH', '')))

    env.append(('Python Prefix', sys.prefix))
    env.append(('Python Exec Prefix', sys.exec_prefix))

    env.append(('Python Version', sys.version))
    env.append(('Python Platform', sys.platform))

    env.append(('Python Max Unicode', sys.maxunicode))

    # Extensions information.

    extensions = []

    if 'newrelic.core._thread_utilization' in sys.modules:
        extensions.append('newrelic.core._thread_utilization')

    if 'newrelic.lib.simplejson._speedups' in sys.modules:
        extensions.append('newrelic.lib.simplejson._speedups')

    env.append(('Compiled Extensions', ', '.join(extensions)))

    # Dispatcher information.

    dispatcher = []

    if not dispatcher and 'mod_wsgi' in sys.modules:
        mod_wsgi = sys.modules['mod_wsgi']
        if hasattr(mod_wsgi, 'process_group'):
            if mod_wsgi.process_group == '':
                dispatcher.append(('Dispatcher', 'Apache/mod_wsgi (embedded)'))
            else:
                dispatcher.append(('Dispatcher', 'Apache/mod_wsgi (daemon)'))
        else:
            dispatcher.append(('Dispatcher', 'Apache/mod_wsgi'))
        if hasattr(mod_wsgi, 'version'):
            dispatcher.append(('Dispatcher Version', str(mod_wsgi.version)))

    if not dispatcher and 'uwsgi' in sys.modules:
        dispatcher.append(('Dispatcher', 'uWSGI'))
        uwsgi = sys.modules['uwsgi']
        if hasattr(uwsgi, 'version'):
            dispatcher.append(('Dispatcher Version', uwsgi.version))

    if not dispatcher and 'flup.server.fcgi' in sys.modules:
        dispatcher.append(('Dispatcher', 'flup/fastcgi (threaded)'))

    if not dispatcher and 'flup.server.fcgi_fork' in sys.modules:
        dispatcher.append(('Dispatcher', 'flup/fastcgi (prefork)'))

    if not dispatcher and 'flup.server.scgi' in sys.modules:
        dispatcher.append(('Dispatcher', 'flup/scgi (threaded)'))

    if not dispatcher and 'flup.server.scgi_fork' in sys.modules:
        dispatcher.append(('Dispatcher', 'flup/scgi (prefork)'))

    if not dispatcher and 'flup.server.ajp' in sys.modules:
        dispatcher.append(('Dispatcher', 'flup/ajp (threaded)'))

    if not dispatcher and 'flup.server.ajp_fork' in sys.modules:
        dispatcher.append(('Dispatcher', 'flup/ajp (forking)'))

    if not dispatcher and 'flup.server.cgi' in sys.modules:
        dispatcher.append(('Dispatcher', 'flup/cgi'))

    if not dispatcher and 'tornado' in sys.modules:
        dispatcher.append(('Dispatcher', 'tornado'))
        tornado = sys.modules['tornado']
        if hasattr(tornado, 'version_info'):
            dispatcher.append(('Dispatcher Version',
                               str(tornado.version_info)))

    if not dispatcher and 'gunicorn' in sys.modules:
        if 'gunicorn.workers.ggevent' in sys.modules:
            dispatcher.append(('Dispatcher', 'gunicorn (gevent)'))
        elif 'gunicorn.workers.geventlet' in sys.modules:
            dispatcher.append(('Dispatcher', 'gunicorn (eventlet)'))
        else:
            dispatcher.append(('Dispatcher', 'gunicorn'))
        gunicorn = sys.modules['gunicorn']
        if hasattr(gunicorn, '__version__'):
            dispatcher.append(('Dispatcher Version', gunicorn.__version__))

    env.extend(dispatcher)

    # Module information.

    plugins = []

    for name, module in sys.modules.items():
        if name.find('.') == -1 and hasattr(module, '__file__'):
            try:
                if 'pkg_resources' in sys.modules:
                    version = pkg_resources.get_distribution(name).version
                    if version:
                        name = '%s (%s)' % (name, version)
            except:
                pass
            plugins.append(name)

    env.append(('Plugin List', plugins))

    return env
