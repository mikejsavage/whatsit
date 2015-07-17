import sys, os, socket, functools, logging

import config
from layer import DomainSocketLayer

from yowsup.stacks           import YowStack, YowStackBuilder
from yowsup.layers           import YowLayerEvent
from yowsup.layers.auth      import AuthError
from yowsup.layers.interface import YowInterfaceLayer
from yowsup.layers.network   import YowNetworkLayer

logging.basicConfig( level = logging.INFO )
logger = logging.getLogger( __name__ )

config.init( sys.argv[ 1 ] )

addr = "/tmp/whatsit_%s.sock" % config.credentials[ "phone" ]
logger.info( "Binding to %s", addr )

os.unlink( addr )
sock = socket.socket( socket.AF_UNIX, socket.SOCK_STREAM )
sock.bind( addr )
sock.listen( 1 )

try:
    while True:
        logger.info( "Waiting for a local client" )
        client, _ = sock.accept()
        fd = client.makefile()
        logger.info( "Local client connected! Connecting to WhatsApp" )

        # We want to use fd in our DomainSocketLayer, so make a shim class
        class ProxyLayer( DomainSocketLayer, YowInterfaceLayer ):
            def __init__( self ):
                self.fd = fd
                super( ProxyLayer, self ).__init__()

        credentials = (
            config.credentials[ "phone" ],
            config.credentials[ "password" ]
        )

        stack = (
            YowStackBuilder()
            .pushDefaultLayers( True )
            .push( ProxyLayer )
            .build()
        )

        stack.setCredentials( credentials )
        stack.broadcastEvent( YowLayerEvent( YowNetworkLayer.EVENT_STATE_CONNECT ) )

        stack.loop()

except AuthError as e:
    print( "Authentication Error: " + e.message )

except KeyboardInterrupt:
    os.unlink( addr )

    sys.exit( 0 )
