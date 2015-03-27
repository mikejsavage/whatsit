import sys, os, yowsup

import config
from layer import EchoLayer

from yowsup.stacks          import YowStack, YowStackBuilder
from yowsup.layers          import YowLayerEvent
from yowsup.layers.auth     import AuthError
from yowsup.layers.network  import YowNetworkLayer

config.init( sys.argv[ 1 ] )

try:
    credentials = (
        config.credentials[ "phone" ],
        config.credentials[ "password" ]
    )

    stack = YowStackBuilder().pushDefaultLayers( True ).push( EchoLayer ).build()
    stack.setCredentials( credentials )
    stack.broadcastEvent( YowLayerEvent( YowNetworkLayer.EVENT_STATE_CONNECT ) )

    stack.loop()

except AuthError as e:
    print( "Authentication Error: " + e.message )

except KeyboardInterrupt:
    os.remove( "in" )
    os.remove( "out" )

    sys.exit( 0 )
