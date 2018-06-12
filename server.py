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
        
        print('Ready to receive requests')
        server.add_sockets(sockets)
        asyncio.get_event_loop().run_forever()
    except Exception as exception:
        print(exception)
        pprint.pprint(traceback.format_tb(exception.__traceback__))


if __name__ == '__main__':
    main()
