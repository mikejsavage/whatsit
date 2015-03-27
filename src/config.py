def init( path ):
    global credentials
    credentials = { }

    with open( path, "r" ) as file:
        lines = file.read().split( "\n" )
        credentials[ "phone" ] = lines[ 0 ]
        credentials[ "password" ] = lines[ 1 ]
