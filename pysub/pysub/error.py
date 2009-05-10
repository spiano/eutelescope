## Base class for errors in Pysub
#
class PysubError( Exception ):
    pass

## Error with Marlin execution
#
class MarlinError( PysubError ):

    def __init__ (self, message, errno ):
        self._message = message
        self._errno   = errno

## Missing generic file
class MissingFileError ( PysubError ):
    def __init__ (self, filename ):
        self._filename = filename


## Missing input file
#
class MissingInputFileError( MissingFileError ):
    pass

## Missing GEAR file
# 
class MissingGEARFileError( MissingFileError ):
    pass

## Missing Steering template
class MissingSteeringTemplateError( MissingFileError ):
    pass

## Missing output file
#
class MissingOutputFileError( MissingFileError ):
    pass

## Problem copying file from GRID
#
class GRID_LCG_CPError( MissingFileError ):
    pass

## Problem copying / registering file to GRID
#
class GRID_LCG_CRError( MissingFileError ):
    pass

## Stop execution error
#
# This error is so critical that the execution has to
# be terminated. 
#
class StopExecutionError( PysubError ):
    def __init__( self, message ):
        self._message = message;
