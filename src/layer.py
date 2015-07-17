from __future__ import print_function

import sys, os, json, logging, threading

import config

from yowsup.layers.interface                           import YowInterfaceLayer, ProtocolEntityCallback
from yowsup.layers.protocol_messages.protocolentities  import TextMessageProtocolEntity
from yowsup.layers.protocol_messages.protocolentities  import BroadcastTextMessage
from yowsup.layers.protocol_receipts.protocolentities  import OutgoingReceiptProtocolEntity
from yowsup.layers.protocol_acks.protocolentities      import OutgoingAckProtocolEntity

logging.basicConfig( level = logging.INFO )
logger = logging.getLogger( __name__ )

class DomainSocketLayer( YowInterfaceLayer ):
    def __init__( self ):
        self.th = threading.Thread( target = self.readSocket )
        self.th.daemon = True
        self.th.start()

        YowInterfaceLayer.__init__( self )

    # Read messages from the socket and forward them to WhatsApp
    def readSocket( self ):
        for line in iter( self.fd.readline, "" ):
            logger.debug( "Received line: %s", line )

            try:
                cmd = json.loads( line )
                outgoing = None

                if cmd[ "action" ] == "message":
                    outgoing = TextMessageProtocolEntity( cmd[ "body" ], to = cmd[ "to" ] )
                elif cmd[ "action" ] == "broadcast":
                    outgoing = BroadcastTextMessage( cmd[ "to" ], cmd[ "body" ] )

                if outgoing:
                    self.toLower( outgoing )
            except:
                logger.error( "Couldn't parse input line! Maybe you're missing the \"action\" field." )
                logger.error( line )

        logger.info( "Local client disconnected. Disconnecting from WhatsApp" )
        self.disconnect()

    # We received a nice message
    def onText( self, msg ):
        logger.debug( "Received message from %s: %s", msg.getFrom(), msg.getBody() )

        # Write JSON to the socket
        self.fd.write( json.dumps( {
            "from" : msg.getFrom(),
            "body" : msg.getBody(),
        } ) + "\n" )
        self.fd.flush()

        # Acknowledge it
        receipt = OutgoingReceiptProtocolEntity( msg.getId(), msg.getFrom() )
        self.toLower( receipt )

    # Check it's a message we care about, then pass it to self.onText
    @ProtocolEntityCallback( "message" )
    def onMessage( self, messageProtocolEntity ):
        if not messageProtocolEntity.isGroupMessage():
            if messageProtocolEntity.getType() == "text":
                self.onText( messageProtocolEntity )
    
    # Boilerplate
    @ProtocolEntityCallback( "receipt" )
    def onReceipt( self, receipt ):
        ack = OutgoingAckProtocolEntity( receipt.getId(), "receipt", "delivery", receipt.getFrom() )
        self.toLower( ack )
