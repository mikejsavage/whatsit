#! /usr/bin/lua

local cqueues = require( "cqueues" )
local thread = require( "cqueues.thread" )
local socket = require( "cqueues.socket" )

if #arg ~= 2 then
	print( "Usage: " .. arg[ 0 ] .. " <incoming> <outgoing>" )
	os.exit( 1 )
end

local incoming = arg[ 1 ]
local outgoing = arg[ 2 ]

local th, ch = thread.start( function( ch, outgoing )
	local cqueues = require( "cqueues" )
	local json = require( "cjson" )

	local loop = cqueues.new()
	local _, sock = ch:recvfd()

	loop:wrap( function()
		while true do
			local line = io.read( "*line" )

			sock:write( json.encode( {
				action = "message",
				body = line,
				to = outgoing,
			} ) .. "\n" )
		end
	end )

	assert( loop:loop() )
end, outgoing .. "@s.whatsapp.net" )

local loop = cqueues.new()
local sock = assert( socket.connect( { path = "/tmp/whatsit_" .. incoming .. ".sock" } ) )

ch:sendfd( "whatsit", sock )

loop:wrap( function()
	for line in sock:lines( "*l" ) do
		print( line )
	end
end )

loop:wrap( function()
	th:join()
end )

assert( loop:loop() )
