#! /usr/bin/env python3
# -*- coding: utf8 -*-
import sys
import getopt
import os.path
import io
import codecs
import json

# ============================= LOCAL CLASSES ======================================
class ErrHandle:
  """Error handling"""

  # ======================= CLASS INITIALIZER ========================================
  def __init__(self):
    # Initialize a local error stack
    self.loc_errStack = []

  # ----------------------------------------------------------------------------------
  # Name :    Status
  # Goal :    Just give a status message
  # History:
  # 6/apr/2016    ERK Created
  # ----------------------------------------------------------------------------------
  def Status(self, msg):
    # Just print the message
    print(msg, file=sys.stderr)

  # ----------------------------------------------------------------------------------
  # Name :    DoError
  # Goal :    Process an error
  # History:
  # 6/apr/2016    ERK Created
  # ----------------------------------------------------------------------------------
  def DoError(self, msg, bExit = False):
    # Append the error message to the stack we have
    self.loc_errStack.append(msg)
    # Print the error message for the user
    print("Error: "+msg+"\nSystem:", file=sys.stderr)
    for nErr in sys.exc_info():
      if (nErr != None):
        print(nErr, file=sys.stderr)
    # Is this a fatal error that requires exiting?
    if (bExit):
      sys.exit(2)


# ============================= LOCAL VARIABLES ====================================
errHandle =  ErrHandle()


# ----------------------------------------------------------------------------------
# Name :    main
# Goal :    Main body of the function
# History:
# 18/jun/2016    ERK Created
# ----------------------------------------------------------------------------------
def main(prgName, argv) :
    flInput = ''        # input file name
    flOutput = ''       # output file name

    try:
        # Adapt the program name to exclude the directory
        index = prgName.rfind("\\")
        if (index > 0) :
            prgName = prgName[index+1:]

        sSyntax = prgName + ' -i <inputfile> -o <outputfile>'
        # get all the arguments
        try:
            # Get arguments and options
            opts, args = getopt.getopt(argv, "hi:o:", ["-inputfile=","-outputfile="])
        except getopt.GetoptError:
            print(sSyntax)
            sys.exit(2)

        # Walk all the arguments
        for opt, arg in opts:
            if opt == '-h':
                print(sSyntax)
                sys.exit(0)
            elif opt in ("-i", "--inputfile"):
                flInput = arg
            elif opt in ("-o", "--outputfile"):
                flOutput = arg

        # Check if all arguments are there
        if (flInput == '' or flOutput == ''):
            errHandle.DoError(sSyntax)

        # Continue with the program
        errHandle.Status('Input is "' + flInput + '"')
        errHandle.Status('Output is "' + flOutput + '"')

        # Call the function that converst input into output
        if (collfix(flInput, flOutput)) :
            errHandle.Status("Ready")
        else :
            errHandle.DoError("Could not complete")

        # return positively
        return True
    except:
        # act
        errHandle.DoError("main")
        return False


# ----------------------------------------------------------------------------------
# Name :    collfix
# Goal :    Create fixtures for the collection bank
# History:
# 18/jun/2016    ERK Created
# ----------------------------------------------------------------------------------
def collfix(csv_file, output_file):
    try:
        # Validate: input file exists
        if (not os.path.isfile(csv_file)): return False

        # Start creating an array that will hold the fixture elements
        arFixture = []
        iPkNum = 1          # Incremental PKs
        iMvNum = 1          # Incremental "machine_value" index per 'field' type
        sCurrentField = ""  # to note changes in field
        sModel = "collection.fieldchoice"
        arFieldNames = []

        # Open source file to read line-by-line
        f = codecs.open(csv_file, "r", encoding='utf-8-sig')
        bEnd = False
        bFirst = True
        while (not bEnd):
            # Read one line
            strLine = f.readline()
            if (strLine == ""):
                break
            strLine = str(strLine)
            strLine = strLine.strip(" \n\r")
            # Only process substantial lines
            if (strLine != ""):
                # Split the line into parts
                arPart = strLine.split('\t')
                # IF this is the first line or an empty line, then skip
                if (not bFirst):
                    # Create a structure for this line
                    oFields = {}
                    for i in range(len(arPart)):
                        oFields[arFieldNames[i]] = arPart[i]

                    # Checking and book-keeping in order to get the right machine_value number
                    if (sCurrentField != oFields["field"]):
                        iMvNum = 1
                        sCurrentField = oFields["field"]
                    if (oFields["machine_value"] == ""):
                        oFields["machine_value"] = iMvNum
                        iMvNum += 1

                    # CReate an array element
                    oEntry = {"model": sModel, "pk": iPkNum, "fields": oFields}

                    # Add the array element
                    arFixture.append(oEntry)

                    # Make sure PK is incremented
                    iPkNum += 1
                else:
                    # Indicate that the first item has been had
                    bFirst = False

                    # Store the field names into the array
                    arFieldNames = arPart

        # CLose the input file
        f.close()

        # COnvert the array into a json string
        sJson = json.dumps(arFixture, indent=2)

        # Save the string to the output file
        fl_out = io.open(output_file, "w", encoding='utf-8')
        fl_out.write(sJson)
        fl_out.close()

        # return positively
        return True
    except:
        errHandle.DoError("collfix")
        return False


# ----------------------------------------------------------------------------------
# Goal :  If user calls this as main, then follow up on it
# History:
# 18/jun/2016    ERK Created
# ----------------------------------------------------------------------------------
if __name__ == "__main__":
  # Call the main function with two arguments: program name + remainder
  main(sys.argv[0], sys.argv[1:])