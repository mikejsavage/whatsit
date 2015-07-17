import sys, os, socket, functools, logging

import config
from layer import DomainSocketLayer

from yowsup.layers.auth              import YowAuthenticationProtocolLayer, AuthError
from yowsup.layers.interface         import YowInterfaceLayer
from yowsup.layers.protocol_messages import YowMessagesProtocolLayer
from yowsup.layers.protocol_receipts import YowReceiptProtocolLayer
from yowsup.layers.protocol_acks     import YowAckProtocolLayer
from yowsup.layers.network           import YowNetworkLayer
from yowsup.layers.coder             import YowCoderLayer

from yowsup.stacks import YowStack
from yowsup.common import YowConstants
from yowsup.layers import YowLayerEvent
from yowsup.stacks import YowStack, YOWSUP_CORE_LAYERS
from yowsup import env

logging.basicConfig( level = logging.INFO )
logger = logging.getLogger( __name__ )

config.init( sys.argv[ 1 ] )

addr = "/tmp/whatsit_%s.sock" % config.credentials[ "phone" ]
logger.info( "Binding to %s", addr )

try:
    os.unlink( addr )
except:
    pass

sock = socket.socket( socket.AF_UNIX, socket.SOCK_STREAM )
sock.bind( addr )
sock.listen( 1 )

try:
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

    layers = (
        ProxyLayer,
        ( YowAuthenticationProtocolLayer, YowMessagesProtocolLayer, YowReceiptProtocolLayer, YowAckProtocolLayer )
    ) + YOWSUP_CORE_LAYERS

    stack = YowStack( layers )
    stack.setProp( YowAuthenticationProtocolLayer.PROP_CREDENTIALS, credentials )
    stack.setProp( YowNetworkLayer.PROP_ENDPOINT, YowConstants.ENDPOINTS[0] )
    stack.setProp( YowCoderLayer.PROP_DOMAIN, YowConstants.DOMAIN )
    stack.setProp( YowCoderLayer.PROP_RESOURCE, env.CURRENT_ENV.getResource() )

    stack.broadcastEvent( YowLayerEvent( YowNetworkLayer.EVENT_STATE_CONNECT ) )

    stack.loop()

except AuthError as e:
    print( "Authentication Error: " + e.message )

except KeyboardInterrupt:
    os.unlink( addr )

    sys.exit( 0 )
