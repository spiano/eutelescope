#!/usr/bin/env python

import sys
import string
import re
import os
import popen2

blue="\033[1;34m"
black="\033[0m"
red="\033[1;31m"
green="\033[1;32m"


def usage( commandname ):

    print green , "Usage:"
    print commandname, "[ OPTIONS ]  run-list"
    print """
          List of OPTIONS
             -h or --help         Print this help message

             -l or --all-local    Execute the job(s) entirely locally
             -r or --all-grid     Execute the job(s) entirely on the GRID
             -c or --cpu-local    Execute the job(s) on the local CPU but get and put data to the GRID SE

             --keep-input         Don't delete the input files when finished
             --keep-output        Don't delete the output files when finished

             --only-generate      Simply genereate the steering file

    """
    print black


# here starts the main
print red, "Pedestal job submitter" , black

# default options
optionAllLocal = 0
optionAllGrid  = 0
optionCPULocal = 1

optionGenerateOnly = 0

optionKeepInput = 1
optionKeepOutput = 1


# defaul GRID paths
gridFolderNative          = "$LFC_HOME/2008/tb-cern-summer/native-depfet"
gridFolderLcioRaw         = "$LFC_HOME/2008/tb-cern-summer/lcio-raw-depfet"
gridFolderDB              = "$LFC_HOME/2008/tb-cern-summer/db-depfet"
gridFolderPedestalHisto   = "$LFC_HOME/2008/tb-cern-summer/joboutput/depfet/pedestal"
gridFolderPedestalJobout  = "$LFC_HOME/2008/tb-cern-summer/joboutput/depfet/pedestal"


# parse the argmuments
narg = 0
runList = []
copiedDBFile = []
copiedHistoFile = []
copiedTARFile = []

for i,arg in enumerate(sys.argv[1:]):
    narg = narg + 1
    if arg == "-l" or arg == "--all-local":
        optionAllLocal = 1
        optionAllGrid  = 0
        optionCPULocal = 0
        optionKeepInput = 1
        optionKeepOutput = 1

    elif arg == "-r" or arg == "--all-grid":
        optionAllLocal = 0
        optionAllGrid  = 1
        optionCPULocal = 0
        optionKeepInput = 0
        optionKeepOutput = 0

    elif arg == "-c" or arg == "--cpu-local":
        optionAllLocal = 0
        optionAllGrid  = 0
        optionCPULocal = 1
        optionKeepInput = 0
        optionKeepOutput = 0

    elif arg == "--keep-input":
        optionKeepInput = 1

    elif arg == "--keep-output":
        optionKeepOutput = 1

    elif arg == "--only-generate":
        optionGenerateOnly = 1
        optionKeepInput = 1
        optionKeepOutput = 1

    elif arg == "-h" or arg == "--help":
        usage(sys.argv[0])
        sys.exit(0)

    else :
        # if it is not one of previuos, then it is a run number
        try:
            runList.append( int( arg ) )

        except ValueError:
            print red, "Unrecognized option (%(option)s), or invalid run number" % { "option": arg }


if narg == 0:
    usage(sys.argv[0])
    sys.exit(0)

if len(runList) == 0:
    print red, "The run list is empty, please specify at least one run to be processed", black
    sys.exit(1)

if optionKeepInput == 0:
    goodAnswer = 0
    while goodAnswer == 0:
        print green, "This script is going to delete the input file(s) when finished.\n" ,\
                  " Are you sure to continue? [y/n]", black
        answer = raw_input( "--> ").lower()
        if answer != "y" and answer != "yes" and answer != "n" and answer != "no":
            print red, "Invalid answer, please type y or n", black
            answer = raw_input( "--> " ).lower()
        elif answer == "y" or answer == "yes":
            goodAnswer = 1
        elif answer == "n" or answer == "no":
            goodAnswer = 1
            sys.exit("Aborted by the user")

if optionKeepOutput == 0:
    goodAnswer = 0
    while goodAnswer == 0:
        print green, "This script is going to delete the output file(s) when finished.\n" ,\
                  " Are you sure to continue? [y/n]", black
        answer = raw_input( "--> ").lower()
        if answer != "y" and answer != "yes" and answer != "n" and answer != "no":
            print red, "Invalid answer, please type y or n", black
            answer = raw_input( "--> " ).lower()
            print "la risp dentro: ", answer
        elif answer == "y" or answer == "yes":
            goodAnswer = 1
        elif answer == "n" or answer == "no":
            goodAnswer = 1
            sys.exit("Aborted by the user")


for run in runList[:]:
    returnvalue = 0
    runString = "%(#)06d" % { "#": run }

    print blue, "Generating the steering file... (pedestal-%(run)s.xml)" % { "run": runString }, black

    # open the template steering file for reading
    templateSteeringFile = open( "./template/pedestal-tmp.xml", "r")

    # read the whole content of the template and put it into a string
    templateSteeringString = templateSteeringFile.read()

    actualSteeringString = templateSteeringString.replace("@RunNumber@", runString )

    actualSteeringFile = open( "pedestal-%(run)s.xml" % { "run": runString }, "w" )
    actualSteeringFile.write( actualSteeringString )

    actualSteeringFile.close()

    templateSteeringFile.close()

    if optionGenerateOnly == 1 :
        continue

    if optionAllGrid == 0 :

        if optionCPULocal == 1:
            print blue, "Getting the input lcio-raw file from the GRID...", black
            command = "lcg-cp -v lfn:%(inputFolder)s/run%(run)s.slcio file:$PWD/lcio-raw/run%(run)s.slcio" % \
                { "inputFolder": gridFolderLcioRaw , "run": runString }
            returnvalue = os.system( command )
            if returnvalue != 0:
                print red, "Problem getting the input file! (errno %(returnvalue)s)" % {"returnvalue":returnvalue }, black
                continue

        # run Marlin in both all local and cpu local configuration
        print blue, "Running Marlin...",black

        # to properly get the return code I need to execute Marlin into a separete pipe
        logfile = open( "pedestal-%(run)s.log " % { "run": runString }, "w" )
        marlin = popen2.Popen4( "Marlin pedestal-%(run)s.xml" % { "run": runString } )
        while marlin.poll() == -1:
            line = marlin.fromchild.readline()
            print line.strip()
            logfile.write( line )

        logfile.close()
        returnvalue = marlin.poll()

        if returnvalue != 0:
            print red, "Problem executing Marlin! (errno %(returnvalue)s)" % {"returnvalue":returnvalue }, black
            continue

        # Copy to the GRID only in CPULocal mode
        if optionCPULocal == 1:
            print blue, "Copying register the output file to the GRID...", black
            command = "lcg-cr -v -l lfn:%(gridFolder)s/run%(run)s-ped-db.slcio file:$PWD/db/run%(run)s-ped-db.slcio" % \
                { "gridFolder": gridFolderDB , "run": runString }
            returnvalue = os.system( command )
            if returnvalue != 0:
                print red, "Problem copying the pedestal DB file to the GRID! (errno %(returnvalue)s)" % {"returnvalue":returnvalue }, black
            else:
                copiedDBFile.append( "%(gridFolder)s/run%(run)s-ped-db.slcio" % { "gridFolder": gridFolderDB , "run": runString } )

            # Copy to the GRID the histo file as well
            print blue, "Copying register the histogram file to the GRID...", black
            command = "lcg-cr -v -l lfn:%(gridFolder)s/run%(run)s-ped-histo.root file:$PWD/histo/run%(run)s-ped-histo.root" % \
                { "gridFolder": gridFolderPedestalHisto , "run": runString }
            returnvalue = os.system( command )
            if returnvalue != 0 :
                print red, "Problem copying the pedestal histogram file to the GRID! (errno %(returnvalue)s)" % {"returnvalue":returnvalue }, black
            else:
                copiedHistoFile.append( "%(gridFolder)s/run%(run)s-ped-histo.root" %  { "gridFolder": gridFolderPedestalHisto , "run": runString } )

        # Prepare the tarbal in any local configurations
        print blue, "Preparing the joboutput tarbal...", black

        # create a temporary folder
        command = "mkdir /tmp/pedestal-%(run)s" % { "run": runString }
        returnvalue = os.system( command )
        if returnvalue != 1 and returnvalue != 0:
            print red, "Problem creating the temporary folder! (errno %(returnvalue)s)" % {"returnvalue":returnvalue}, black
        else:
            # copy there all the tarbal stuff
            command = "cp pedestal-%(run)s* histo/run%(run)s-ped-histo.root /tmp/pedestal-%(run)s" % { "run" : runString }
            returnvalue = os.system( command )
            if returnvalue != 0:
                print red, "Problem copying the joboutput files in the temporary folder! (errno %(returnvalue)s)" % {"returnvalue":returnvalue }, black
            else:
                # tar gzipped the temp folder
                command = "tar czvf pedestal-%(run)s.tar.gz /tmp/pedestal-%(run)s"  % { "run" : runString }
                returnvalue = os.system( command )
                if returnvalue != 0:
                    print red, "Problem tar gzipping the temporary folder! (errno %(returnvalue)s)" % {"returnvalue":returnvalue }, black
                else:

                    # copy the tarbal to the GRID
                    if optionCPULocal == 1:
                        print blue, "Copying the joboutput tarbal to the GRID...", black
                        command = "lcg-cr -v -l lfn:%(gridFolder)s/pedestal-%(run)s.tar.gz file:$PWD/pedestal-%(run)s.tar.gz" % \
                                  { "gridFolder": gridFolderPedestalJobout , "run": runString }
                        returnvalue = os.system( command )
                        if returnvalue != 0:
                            print red, "Problem copying to the GRID! (errno %(returnvalue)s)" % {"returnvalue":returnvalue }, black
                        else:
                            copiedTARFile.append( "%(gridFolder)s/pedestal-%(run)s.tar.gz" \
                                                  %  { "gridFolder": gridFolderPedestalJobout , "run": runString } )
        
        # clean up the execution envirotment
        print blue, "Cleaning up enviroment", black
        command = "rm -vrf /tmp/pedestal-%(run)s pedestal-%(run)s*" % { "run": runString }
        returnvalue = os.system( command )
        if returnvalue != 0:
            print red, "Problem removing temporary files! (errno %(returnvalue)s)" % {"returnvalue":returnvalue }, black
 
        if optionKeepOutput == 0 and optionKeepInput == 0:
            command = "rm -v lcio-raw/run%(run)s.slcio db/run%(run)s-ped-db.slcio histo/run%(run)s-ped-histo.root" % { "run": runString }
            returnvalue = os.system( command )
            if returnvalue != 0:
                print red, "Problem removing the input and output files! (errno %(returnvalue)s)" % {"returnvalue":returnvalue }, black

        elif optionKeepOutput == 1 and optionKeepInput == 0:
            command = "rm -v lcio-raw/run%(run)s.slcio" % { "run": runString }
            returnvalue = os.system( command )
            if returnvalue != 0:
                print red, "Problem removing the input file! (errno %(returnvalue)s)" % {"returnvalue":returnvalue }, black

        elif optionKeepOutput == 0 and optionKeepInput == 1:
            command = "rm -v db/run%(run)s-ped-db.slcio histo/run%(run)s-ped-histo.root" % { "run": runString }
            returnvalue = os.system( command )
            if returnvalue != 0:
                print red, "Problem removing the output file! (errno %(returnvalue)s)" % {"returnvalue":returnvalue }, black

    else :
        print red, "All GRID submission not yet implemented!", blacl

if len(copiedDBFile) != 0 or len(copiedTARFile) != 0 or len(copiedHistoFile) != 0:
    print green, "Summary"
    print " The following pedestal-db file(s) were copied to the GRID:", blue
    for file in copiedDBFile[:] :
        print "\t ", file

    print "\n", green , "The following histo(s) were copied to the GRID:", blue
    for file in copiedHistoFile[:] :
        print "\t ", file

    print "\n", green , "The following tarbal(s) were copied to the GRID:", blue
    for file in copiedTARFile[:] :
        print "\t ", file

    print black
