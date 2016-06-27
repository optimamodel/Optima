import sys
import os

from twisted.internet import reactor
from twisted.internet.endpoints import serverFromString
from twisted.logger import globalLogBeginner, FileLogObserver, formatEvent
from twisted.web.resource import Resource
from twisted.web.server import Site
from twisted.web.static import File
from twisted.web.wsgi import WSGIResource
from twisted.python.threadpool import ThreadPool

globalLogBeginner.beginLoggingTo([
    FileLogObserver(sys.stdout, lambda _: formatEvent(_) + "\n")])

import api

threadpool = ThreadPool(maxthreads=30)
threadpool.start()
wsgi_app = WSGIResource(reactor, threadpool, api.app)

class OptimaResource(Resource):
    isLeaf = True

    def __init__(self, wsgi):
        self._wsgi = wsgi

    def render(self, request):
        request.prepath = []
        request.postpath = ['api'] + request.postpath[:]
        return self._wsgi.render(request)


base_resource = File('client/source/')
base_resource.putChild('build', File('client/source/'))
base_resource.putChild('api', OptimaResource(wsgi_app))

site = Site(base_resource)

try:
    port = str(sys.argv[1])
except IndexError:
    port = "8080"


def run():
    """
    Run the server.
    """
    endpoint = serverFromString(reactor, "tcp:port=" + port)
    endpoint.listen(site)

    reactor.run()

if __name__ == "__main__":
    run()
