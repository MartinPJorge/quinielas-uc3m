from QuinielaScraper import QuinielaScraper
from SheetsOperator import SheetsOperator
from SheetsOperator import SheetsOperator
from QuinielaScraper import QuinielaScraper
import os
import json
import time
import re




class State:
    NEW        = 1
    COMPLETED  = 2
    FINISHED   = 3


class QuinielaDaemon():

    """Class for quiniela's daemon"""

    def __init__(self, quiniScraper, sheetsOp, numDoubles):
        """
        :quiniScraper: scraper for quinielas instance
        :sheetsOp: sheets operator instance
        :self.numDoubles: number of doubles to bet
        """

        self.quiniScraper = quiniScraper
        self.sheetsOp = sheetsOp
        self.sheetId = None
        self.sheetTitle = None
        self.numDoubles = numDoubles
        self.newInState = False
        self.numFootballDay = None
        


    def enterNew(self):
        """Do the operations needed when a new football day is created
        :returns: None

        """
        # Create new football day sheet
        self.printLog(State.NEW, 'creating Jornada ' +
                str(self.numFootballDay))
        self.sheetsOp.deleteSheet(self.sheetId)
        self.sheetId = self.sheetsOp.createFootballDay(self.numFootballDay)
        self.sheetTitle = 'Jornada ' + str(self.numFootballDay)

        # Set scraper for new day, and get matches
        self.printLog(State.NEW, 'downloading matches for: ' + self.sheetTitle)
        self.quiniScraper.getFootballDay(self.numFootballDay)
        matches = self.quiniScraper.getMatches()

        # Fill matches
        self.sheetsOp.fillMatches(matches, self.sheetTitle)


    def getCurrState(self):
        """Determines what is the current state in the quinielas spreadsheet
        :returns: State

        """

        # New sheet created for a football Day
        self.numFootballDay, self.sheetId =\
            self.sheetsOp.checkBornFootballDay()
        self.sheetTitle = 'Jornada ' + str(self.numFootballDay)

        if self.numFootballDay:
            self.newInState = True
            return State.NEW
        # No new football day created
        else:
            # Get last football day data
            self.sheetId, self.sheetTitle = self.sheetsOp.getLastFootballDay()
            self.numFootballDay = re.search('\d+$', self.sheetTitle)
            self.numFootballDay = int(self.numFootballDay.group(0))

            # Not filled columns from people
            if not self.sheetsOp.colsFilled(self.sheetTitle):
                self.newInState = False
                return State.NEW

            # People completed columns
            if not self.sheetsOp.footballDayFinished(self.sheetTitle):
                self.newInState = False
                # Doubles column not filled
                if not self.sheetsOp.doublesFilled(self.sheetTitle,
                        self.numDoubles):
                    self.newInState = True
                return State.COMPLETED
            else:
                return State.FINISHED

        
    def printLog(self, state, msg):
        """Prints a msg in log format

        :state: (State) current state
        :msg: message to be printed
        :returns: None

        """
        stateStr = ''
        if state == State.NEW:
            stateStr = 'NEW'
        elif state == State.COMPLETED:
            stateStr = 'COMPLETED'
        elif state == State.FINISHED:
            stateStr = 'FINISHED'

        print('[' + self.sheetTitle + '] - ' + stateStr + ' - ' + msg)


    def loop(self):
        """Executes the main loop of the daemon
        :returns: None

        """
        print('Getting current state')
        currSt = self.getCurrState()
        justEntered = True
        firstWait = True

        
        ###############
        ## MAIN LOOP ##
        ###############
        while True:
            waitTime = 0

            # NEW QUINIELA
            if currSt == State.NEW:
                if justEntered:
                    self.printLog(currSt, 'just entered')
                    justEntered = False
                    firstWait = True
                if self.newInState:
                    self.printLog(currSt, 'setting up')
                    self.enterNew()
                    self.newInState = False
                elif self.sheetsOp.colsFilled(self.sheetTitle):
                    self.printLog(currSt, 'columns filled!')
                    currSt = State.COMPLETED
                    justEntered = True
                    self.newInState = True
                else:
                    if firstWait:
                        self.printLog(currSt, 'waiting cols to be filled')
                        firstWait = False
                    waitTime = config['periodNew']

            # COMPLETED QUINIELA
            if currSt == State.COMPLETED:
                if justEntered:
                    self.printLog(currSt, 'just entered')
                    justEntered = False
                    firstWait = True
                if self.newInState:
                    self.printLog(currSt, 'fill doubles')
                    self.sheetsOp.fillDoubles(self.sheetTitle, self.numDoubles)
                    self.newInState = False
                elif self.sheetsOp.footballDayFinished(self.sheetTitle):
                    self.printLog(currSt, 'football day finished')
                    currSt = State.FINISHED
                    justEntered = True
                    self.newInState = True
                else:
                    # Get results
                    self.quiniScraper.getFootballDay(self.numFootballDay)
                    matches = self.quiniScraper.getMatches()
                    self.sheetsOp.fillResults(matches, self.sheetTitle)

                    if firstWait:
                        self.printLog(currSt, 'waiting football day end')
                        firstWait = False
                    waitTime = config['periodCompleted']

            # FINISHED QUINIELA
            if currSt == State.FINISHED:
                if justEntered:
                    self.printLog(currSt, 'just entered')
                    justEntered = False
                    firstWait = True
                self.numFootballDay, self.sheetId =\
                    self.sheetsOp.checkBornFootballDay()
                if self.numFootballDay:
                    self.printLog(currSt, ' new football day detected!')
                    currSt = State.NEW
                    justEntered = False
                    self.newInState = True
                else:
                    if firstWait:
                        self.printLog(currSt, 'waiting for new sheet')
                        firstWait = False
                    waitTime = config['periodFinished']

            time.sleep(waitTime)



if __name__ == '__main__':
    # Initialization
    print('Reading config')
    fConf = open('config.json', 'r')
    config = json.load(fConf)
    print ('Creating sheets operator')
    sheetsOp = SheetsOperator(
            config['secretFile'], 
            config['credentials'],
            config['spreadSheetId'],
            config['plantillaId'],
            config['appName'],
            config['people'])
    sheetsOp.startService()
    numDoubles = config['numDoubles']
    print('Creating scraper')
    quiniScraper = QuinielaScraper('2016_2017')

    print('Creating daemon')
    quiniDaemon = QuinielaDaemon(quiniScraper, sheetsOp, numDoubles)

    # Enter main loop
    print('Entering main loop')
    quiniDaemon.loop()


