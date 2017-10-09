import getopt
import sys
from struct import *
import pdb

def enum(**named_values):
    return type('Enum', (), named_values)
recordTypes = enum(Debit = "\x00", Credit = "\x01", StartAutopay = "\x02", EndAutopay = "\x03")

headerFormat = '!4sBI'
headerSize = 9
typeFormat = 'c'
typeSize = 1
amountRecordFormat = '!iqd'
autopayRecordFormat = '!iq'
timestampSize = 4
userIdSize = 8
amountSize = 8
targetUser = 2456938384156277127L

header = ''
paymentsInName = ''

def main(argv):
    #recordTypes = enum(Debit = \x00, Credit = \x01, StartAutopay = \x02, EndAutopay = \x03)
    readOptions (argv)

    totalDebits, totalCredits, autoPaysStarted, autoPaysEnded, targetUserBalance = processPayments(paymentsInName)

    reportPayments(totalDebits, totalCredits, autoPaysStarted, autoPaysEnded, targetUserBalance)

    return True

def reportPayments(totalDebits, totalCredits, autoPaysStarted, autoPaysEnded, targetUserBalance):

    print '{} ${}'.format("Total Debits:", totalDebits)
    print '{} ${}'.format("Total Credits:", totalCredits)
    print '{} {}'.format(autoPaysStarted, "autopays started")
    print '{} {}'.format(autoPaysEnded, "autopays ended")
    print '{} {} {} ${:.2f}'.format("User", targetUser, "Balance:", targetUserBalance)


def processPayments(fileName):
    with open(fileName, "r+b") as f:
        readHeader(f)
        totalDebits, totalCredits, autoPaysStarted, autoPaysEnded, targetUserBalance = readPayments(f)

    return (totalDebits, totalCredits, autoPaysStarted, autoPaysEnded, targetUserBalance)

def readHeader(handle):
    rawHeader = handle.read(headerSize)
    magic, version, expectedRecords = unpack(headerFormat, rawHeader)
    #input record count index appeart to starts at 0.
    print 'Protocol: {}, Version: {}, Records: {}'.format(magic, version, expectedRecords + 1)

def readOptions(argv):
    global paymentsInName
    try:
      opts, args = getopt.getopt(argv,"hp:", ["help", "payments="])
    except getopt.GetoptError:
      print 'paymentProcessor.py -p <payment data file>'
      sys.exit(2)
    for opt, arg in opts:
      if opt in ("-h", "--help"):
          print 'paymentProcessor.py -p <payment data file>'
      elif opt in ("-p", "--payments"):
          paymentsInName = arg
      else:
          paymentsInName ='data.dat'

def readPayments(handle):
    #Record:    | 1 byte record type enum | 4 byte (uint32) Unix timestamp | 8 byte (uint64) user ID |
    recordsRead = 0
    userId = 0
    timestamp = 0
    amount = 0
    targetUserBalance = 0
    autoPaysStarted = 0
    autoPaysEnded = 0
    totalDebits = 0
    totalCredits = 0

    while True:
        rawType = handle.read(typeSize)
        if not rawType:
            break
        recordsRead += 1
        if rawType == recordTypes.Debit:
            #process Debit
            rawDebitRecord = handle.read(timestampSize + userIdSize + amountSize)
            timestamp, userId, amount = unpack(amountRecordFormat, rawDebitRecord)
            totalDebits += round(amount, 2)
            #print '{} {} {}'.format(timestamp, userId, amount)
        elif rawType == recordTypes.Credit:
            #process Credit
            rawCreditRecord = handle.read(timestampSize + userIdSize + amountSize)
            timestamp, userId, amount = unpack(amountRecordFormat, rawCreditRecord)
            totalCredits += round(amount, 2)
            #print '{} {} {}'.format(timestamp, userId, amount)
        elif rawType == recordTypes.StartAutopay:
            #process start autopay
            autoPaysStarted += 1
            rawRecord = handle.read(timestampSize + userIdSize)
            timestamp, userId = unpack(autopayRecordFormat, rawRecord)
            #print '{} {}'.format(timestamp, userId)
        elif rawType == recordTypes.EndAutopay:
            #process start autopay
            autoPaysEnded += 1
            rawRecord = handle.read(timestampSize + userIdSize)
            timestamp, userId = unpack(autopayRecordFormat, rawRecord)
            #print '{} {}'.format(timestamp, userId)
        else:
            print '{} {}'.format(rawType, "is invalid")
        #pdb.set_trace()
        if userId == targetUser:
            if rawType == recordTypes.Debit:
                targetUserBalance -= round(amount)
            elif rawType == recordTypes.Credit:
                targetUserBalance += round(amount)

    return (totalDebits, totalCredits, autoPaysStarted, autoPaysEnded, targetUserBalance)


if __name__=='__main__':
    main(sys.argv[1:])
