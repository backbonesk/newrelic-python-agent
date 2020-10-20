# Copyright 2010 New Relic, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from starlette.applications import Starlette
from starlette.background import BackgroundTasks
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.exceptions import HTTPException
from testing_support.asgi_testing import AsgiTest
from newrelic.api.transaction import current_transaction
from newrelic.api.function_trace import FunctionTrace
from newrelic.common.object_names import callable_name

try:
    from starlette.middleware import Middleware
except ImportError:
    Middleware = None


class HandledError(Exception):
    pass


class NonAsyncHandledError(Exception):
    pass


async def index(request):
    return PlainTextResponse("Hello, world!")


def non_async(request):
    assert current_transaction()
    return PlainTextResponse("Not async!")


async def runtime_error(request):
    raise RuntimeError("Oopsies...")


async def handled_error(request):
    raise HandledError("it's cool")


def non_async_handled_error(request):
    raise NonAsyncHandledError("No problems here!")


async def async_error_handler(request, exc):
    return PlainTextResponse("Dude, your app crashed - async style", status_code=500)


def non_async_error_handler(request, exc):
    return PlainTextResponse("Dude, your app crashed", status_code=500)


async def teapot(request, exc=None):
    if exc:
        return PlainTextResponse("Teapot", status_code=418)
    else:
        raise HTTPException(418, "I'm a teapot")

class CustomRoute(object):
    def __init__(self, route):
        self.route = route

    async def __call__(self, scope, receive, send):
        await send({"type": "http.response.start", "status": 200})
        with FunctionTrace(name=callable_name(self.route)):
            await self.route(None)


async def run_bg_task(request):
    tasks = BackgroundTasks()
    tasks.add_task(bg_task_async)
    tasks.add_task(bg_task_non_async)
    return PlainTextResponse("Hello, world!", background=tasks)


async def bg_task_async():
    pass


def bg_task_non_async():
    pass

routes = [
    Route("/index", index),
    Route("/418", teapot),
    Route("/non_async", non_async),
    Route("/runtime_error", runtime_error),
    Route("/handled_error", handled_error),
    Route("/non_async_handled_error", non_async_handled_error),
    Route("/raw_runtime_error", CustomRoute(runtime_error)),
    Route("/raw_http_error", CustomRoute(teapot)),
    Route("/run_bg_task", run_bg_task),
]


def middleware(app):
    async def middleware(scope, receive, send):
        return await app(scope, receive, send)

    return middleware

async def middleware_decorator(request, call_next):
    return await call_next(request)


# Generating target applications
app_name_map = {
    "no_error_handler": (True, False),
    "async_error_handler_no_middleware": (False, False),
    "non_async_error_handler_no_middleware": (False, False),
    "no_middleware": (False, False),
    "debug_no_middleware": (False, True),
    "teapot_exception_handler_no_middleware": (False, False),
}


target_application = dict()
for app_name, flags in app_name_map.items():
    # Bind flags
    middleware_on, debug = flags

    # Instantiate app
    if not middleware_on:
        app = Starlette(debug=debug, routes=routes)
    else:
        if Middleware:
            app = Starlette(debug=debug, routes=routes, middleware=[Middleware(middleware)])
        else:
            app = Starlette(debug=debug, routes=routes)
            # in earlier versions of starlette, middleware is not a legal argument on the Starlette application class
            # In order to keep the counts the same, we add the middleware twice using the add_middleware interface
            app.add_middleware(middleware)

        app.add_middleware(middleware)
        app.middleware("http")(middleware_decorator)

    # Adding custom exception handlers
    app.add_exception_handler(HandledError, async_error_handler)
    app.add_exception_handler(NonAsyncHandledError, non_async_error_handler)

    # Assign to dict
    target_application[app_name] = AsgiTest(app)

# Add custom error handlers
target_application["async_error_handler_no_middleware"].asgi_application.add_exception_handler(Exception, async_error_handler)
target_application["non_async_error_handler_no_middleware"].asgi_application.add_exception_handler(Exception, non_async_error_handler)
target_application["teapot_exception_handler_no_middleware"].asgi_application.add_exception_handler(418, teapot)
