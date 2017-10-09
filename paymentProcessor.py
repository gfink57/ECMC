import getopt, logging, sys
from struct import *

def enum(**named_values):
    return type('Enum', (), named_values)
recordTypes = enum(Debit = "\x00", Credit = "\x01", StartAutopay = "\x02", EndAutopay = "\x03")

#set up logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
logger.addHandler(handler)

targetUser = 2456938384156277127L

header = ''
paymentsInName = ''

def main(argv):
    readOptions (argv)
    #extract and count the records 
    totalDebits, totalCredits, autoPaysStarted, autoPaysEnded, targetUserBalance = processPayments(paymentsInName)
    #write a simple report
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
    #Data file header format (no delimiters between records):
    #| 4 byte magic string "MPS7" | 1 byte version | 4 byte (uint32) # of records |
    magicStringSize = 4
    versionSize = 1
    recordCountSize = 4

    #record format for unpack function
    headerFormat = '!4sBI'

    rawHeader = handle.read(magicStringSize + versionSize + recordCountSize)
    magic, version, expectedRecords = unpack(headerFormat, rawHeader)
    #input record count index appeart to starts at 0, so we should read (expectedRecords + 1) records
    print 'Protocol: {}, Version: {}, Records: {}'.format(magic, version, expectedRecords)

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
    #Record format (no delimiters between records):
    #| 1 byte record type enum | 4 byte (uint32) Unix timestamp | 8 byte (uint64) user ID | {8 byte (float64) amount }
    amountSize = 8
    timestampSize = 4
    typeSize = 1
    userIdSize = 8

    #record formats for unpack functions
    amountRecordFormat = '!iqd'
    autopayRecordFormat = '!iq'
    typeFormat = 'c'

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
        #recordTypes = enum(Debit = \x00, Credit = \x01, StartAutopay = \x02, EndAutopay = \x03)
        if rawType == recordTypes.Debit:
            #process Debit
            rawDebitRecord = handle.read(timestampSize + userIdSize + amountSize)
            timestamp, userId, amount = unpack(amountRecordFormat, rawDebitRecord)
            totalDebits += round(amount, 2)
            logger.debug('{} {} {}'.format(timestamp, userId, amount))
        elif rawType == recordTypes.Credit:
            #process Credit
            rawCreditRecord = handle.read(timestampSize + userIdSize + amountSize)
            timestamp, userId, amount = unpack(amountRecordFormat, rawCreditRecord)
            totalCredits += round(amount, 2)
            logger.debug('{} {} {}'.format(timestamp, userId, amount))
        elif rawType == recordTypes.StartAutopay:
            #process start autopay
            autoPaysStarted += 1
            rawRecord = handle.read(timestampSize + userIdSize)
            timestamp, userId = unpack(autopayRecordFormat, rawRecord)
            logger.debug('{} {}'.format(timestamp, userId))
        elif rawType == recordTypes.EndAutopay:
            #process start autopay
            autoPaysEnded += 1
            rawRecord = handle.read(timestampSize + userIdSize)
            timestamp, userId = unpack(autopayRecordFormat, rawRecord)
            logger.debug('{} {}'.format(timestamp, userId))
        else:
            logger.INFO('{} {}'.format(rawType, "is invalid"))

        if userId == targetUser:
            if rawType == recordTypes.Debit:
                targetUserBalance -= round(amount)
            elif rawType == recordTypes.Credit:
                targetUserBalance += round(amount)

    return (totalDebits, totalCredits, autoPaysStarted, autoPaysEnded, targetUserBalance)


if __name__=='__main__':
    main(sys.argv[1:])
