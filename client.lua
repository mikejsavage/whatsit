#! /usr/bin/lua

local cqueues = require( "cqueues" )
local thread = require( "cqueues.thread" )

local number = assert( arg[ 1 ], "need a number" ) .. "@s.whatsapp.net"

local th = thread.start( function( con, number )
	local cqueues = require( "cqueues" )
	local fifo_in = io.open( "in", "w" )
	local json = require( "cjson" )

	while true do
		local line = io.read( "*line" )

		fifo_in:write( json.encode( {
			body = line,
			to = number,
		} ) .. "\n" )
		fifo_in:flush()
	end
end, number )

local th2 = thread.start( function()
	local cqueues = require( "cqueues" )
	local fifo_out = io.open( "out", "r" )

	while true do
		local line = fifo_out:read( "*line" )
		if line then
			print( line )
		else
			fifo_out:close()
			fifo_out = io.open( "out", "r" )
		end
	end
end )

th:join()
th2:join()
