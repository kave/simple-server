from ddtrace import patch

patch(tornado=True)
patch(asyncio=True)
import asyncio  # noqa: E402
import functools  # noqa: E402
import logging  # noqa: E402
import signal  # noqa: E402

import tornado.netutil  # noqa: E402
import tornado.process  # noqa: E402
from datadog import initialize  # noqa: E402
from tornado.httpserver import HTTPServer  # noqa: E402
from tornado.web import Application  # noqa: E402
import traceback  # noqa: E402
import pprint  #noqa: E402


async def signal_handler(sig):
    """
    This method will be used to catch any Signal that is being sent to the service. It will
    check whether there are any running process. If there are any then it will just log
    which process are running and along with that it would help in not shutting down the
    process that are running.

    Currently this method is used for catching SIGTERM as kubernetes calls SIGTERM and waits for 30
    seconds before calling SIGKILL which is used for shutting down the pod/service.
    Please check this doc for more info: https://pracucci.com/graceful-shutdown-of-kubernetes-pods.html

    :param sig: Any type of signal
    """
    tasks = [task for task in asyncio.Task.all_tasks() if task is not
             asyncio.tasks.Task.current_task()]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    for task in list(filter(None.__ne__, results)):
        try:
            print('SIGNAL_CAUGHT_TRANSACTION_PENDING')
        except Exception as exception:
            pass


def main():
    try:
        sockets = tornado.netutil.bind_sockets(9000)
        """
        Tornado AsyncIO integration needs to fork processes before asyncio event loop gets initiated per process
        http://www.tornadoweb.org/en/stable/asyncio.html
        https://stackoverflow.com/questions/42767635
        """
        tornado.process.fork_processes(1)
        # Initialize Datadog
        initialize(statsd_host='localhost', statsd_port='8125')
        DD_SETTINGS = {
            'datadog_trace': {
                'default_service': 'simpleServer',
                'tags': {'env': 'local'},
                'enabled': True,
                'distributed_tracing': False,
            },
        }
        app = Application(**DD_SETTINGS)

        # Disabling tornado logging
        logging.getLogger('tornado.access').disabled = True
        server = HTTPServer(app)

        # Adding signal handler for SIGTERM signal
        asyncio.get_event_loop().add_signal_handler(signal.SIGTERM, functools.partial(asyncio.ensure_future,
                                                                                      signal_handler(signal.SIGTERM)))

        print('Ready to receive requests')
        server.add_sockets(sockets)
        asyncio.get_event_loop().run_forever()
    except Exception as exception:
        print(exception)
        pprint.pprint(traceback.format_tb(exception.__traceback__))


if __name__ == '__main__':
    main()
