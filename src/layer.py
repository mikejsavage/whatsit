from __future__ import print_function

import sys, os, json, threading

from yowsup.layers.interface                           import YowInterfaceLayer, ProtocolEntityCallback
from yowsup.layers.protocol_messages.protocolentities  import TextMessageProtocolEntity
from yowsup.layers.protocol_receipts.protocolentities  import OutgoingReceiptProtocolEntity
from yowsup.layers.protocol_acks.protocolentities      import OutgoingAckProtocolEntity

# This class creates the input pipe and spawns a thread to read it
# Each line we read is parsed as JSON and treated as a message
class StdinReader( object ):
    def __init__( self ):
        os.mkfifo( "in" )

        self.th = threading.Thread( target = self.input )
        self.th.daemon = True
        self.th.start()

    def input( self ):
        # Loop forever incase the other side closes the pipe
        while True:
            with open( "in", "r" ) as fifo:
                for line in iter( fifo.readline, "" ):
                    print( line )
                    try:
                        cmd = json.loads( line )
                        outgoing = TextMessageProtocolEntity( cmd[ "body" ], to = cmd[ "to" ] )
                        self.toLower( outgoing )
                    except:
                        print( "Bad line:", line, file = sys.stderr )

class EchoLayer( StdinReader, YowInterfaceLayer ):
    def __init__( self ):
        # Start the input thread
        super( EchoLayer, self ).__init__()
        YowInterfaceLayer.__init__( self )

        os.mkfifo( "out" )
        self.fifo_out = open( "out", "w" )

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
        try:
            self.fifo_out.write( json.dumps( {
                "from" : msg.getFrom(),
                "body" : msg.getBody(),
            } ) + "\n" )
            self.fifo_out.flush()

            # Acknowledge the incoming message
            receipt = OutgoingReceiptProtocolEntity( msg.getId(), msg.getFrom() )
            self.toLower( receipt )
        except IOError:
            # Reopen the pipe if the other side closes it
            self.fifo_out.close()
            self.fifo_out = open( "out", "w" )
