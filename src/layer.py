from __future__ import print_function

import sys, os, json, threading, socket

import config

from yowsup.layers.interface                           import YowInterfaceLayer, ProtocolEntityCallback
from yowsup.layers.protocol_messages.protocolentities  import TextMessageProtocolEntity
from yowsup.layers.protocol_messages.protocolentities  import BroadcastTextMessage
from yowsup.layers.protocol_receipts.protocolentities  import OutgoingReceiptProtocolEntity
from yowsup.layers.protocol_acks.protocolentities      import OutgoingAckProtocolEntity

# This class creates the input pipe and spawns a thread to read it
# Each line we read is parsed as JSON and treated as a message
class SocketReader( object ):
    def __init__( self ):
        addr = "/tmp/whatsit_%s.sock" % config.credentials[ "phone" ]
        try:
            os.unlink( addr )
        except OSError:
            if os.path.exists( addr ):
                raise

        self.sock = socket.socket( socket.AF_UNIX, socket.SOCK_STREAM )
        self.sock.bind( addr )
        self.sock.listen( 1 )

        self.th = threading.Thread( target = self.accept )
        self.th.daemon = True
        self.th.start()

    def accept( self ):
        # Loop forever incase the other side closes the pipe
        while True:
            self.client, _ = self.sock.accept()
            fd = self.client.makefile()

            for line in iter( fd.readline, "" ):
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
                    print( "Bad line:", line, file = sys.stderr )

            self.client.close()
            self.client = None

class EchoLayer( SocketReader, YowInterfaceLayer ):
    def __init__( self ):
        # Start the input thread
        super( EchoLayer, self ).__init__()
        YowInterfaceLayer.__init__( self )

        self.client = None

    @ProtocolEntityCallback( "message" )
    def onMessage( self, messageProtocolEntity ):
        if not messageProtocolEntity.isGroupMessage():
            if messageProtocolEntity.getType() == "text":
                self.onText( messageProtocolEntity )
    
    # Boilerplate
    @ProtocolEntityCallback( "receipt" )
    def onReceipt( self, receipt ):
        ack = OutgoingAckProtocolEntity( receipt.getId(), "receipt", "delivery" )
        self.toLower( ack )

    def onText( self, msg ):
        if self.client:
            self.client.sendall( json.dumps( {
                "from" : msg.getFrom(),
                "body" : msg.getBody(),
            } ) + "\n" )

            # Acknowledge the incoming message
            receipt = OutgoingReceiptProtocolEntity( msg.getId(), msg.getFrom() )
            self.toLower( receipt )
