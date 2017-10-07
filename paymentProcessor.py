import sys
from struct import *

headerFormat = ''
recordFormat = ''
amountFormat = ''

totalDebits = 0
totalCredits = 0
autopaysStarted = 0
autopaysEnded =    0

specificUserBalance = 0
specificUser = '2456938384156277127'

def main(*args):
    print sys.argv[1]

    header = readHeader()
    if header == '':
          print("Invalid header: " + header)
    else:
          print("processing records")

    return True

def readRecord(recordType):
    return ''

def readHeader():
    header = ''
    return header

if __name__=='__main__':
    main(*sys.argv[1:])
