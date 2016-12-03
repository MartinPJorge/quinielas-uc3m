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
        print('\tCreating Jornada ' + str(self.numFootballDay))
        self.sheetsOp.deleteSheet(self.sheetId)
        self.sheetId = self.sheetsOp.createFootballDay(self.numFootballDay)
        self.sheetTitle = 'Jornada ' + str(self.numFootballDay)

        # Set scraper for new day, and get matches
        print('\tDownloading matches for: ' + self.sheetTitle)
        self.quiniScraper.getFootballDay(self.numFootballDay)
        matches = self.quiniScraper.getMatches()

        # Fill matches
        self.sheetsOp.fillMatches(matches, self.sheetTitle)


    def getCurrState(self):
        """Determines what is the current state in the quinielas spreadsheet
        :returns: State

        """

        # New sheet created for a football Day
        self.numFootballDay, self.sheetId = self.sheetsOp.checkBornFootballDay()
        self.sheetTitle = 'Jornada ' + str(self.numFootballDay)

        if self.numFootballDay:
            self.newInState = True
            print('a')
            return State.NEW
        # No new football day created
        else:
            # Get last football day data
            self.sheetId, self.sheetTitle = self.sheetsOp.getLastFootballDay()
            print('titulo: ' + self.sheetTitle)
            self.numFootballDay = re.search('\d+$', self.sheetTitle)
            self.numFootballDay = int(self.numFootballDay.group(0))

            print('Last: ' + self.sheetTitle)
            if not self.sheetsOp.colsFilled(self.sheetTitle):
                self.newInState = False
                print('b')
                return State.NEW

            # People completed columns
            if not self.sheetsOp.footballDayFinished(self.sheetTitle):
                self.newInState = False
                # Doubles column not filled
                if not self.sheetsOp.doublesFilled(self.sheetTitle,
                        self.numDoubles):
                    self.newInState = True
                    print('c new')
                print('c')
                return State.COMPLETED
            else:
                print('e')
                return State.FINISHED

        print('e')
        


    def loop(self):
        """Executes the main loop of the daemon
        :returns: None

        """
        print('Getting current state')
        currSt = self.getCurrState()

        
        ###############
        ## MAIN LOOP ##
        ###############
        while True:
            waitTime = 0

            # NEW QUINIELA
            if currSt == State.NEW:
                if self.newInState:
                    print('NEW - setting up')
                    self.enterNew()
                    self.newInState = False
                elif self.sheetsOp.colsFilled(self.sheetTitle):
                    print('NEW - columns filled, go to COMPLETED')
                    currSt = State.COMPLETED
                    self.newInState = True
                else:
                    print('Espero')
                    waitTime = config['periodNew']

            # COMPLETED QUINIELA
            if currSt == State.COMPLETED:
                if self.newInState:
                    print('COMPLETED - fill doubles')
                    self.sheetsOp.fillDoubles(self.sheetTitle, self.numDoubles)
                    self.newInState = False
                elif self.sheetsOp.footballDayFinished(self.sheetTitle):
                    print('COMPLETED - football day finished')
                    currSt = State.FINISHED
                    self.newInState = True
                else:
                    # Get results
                    print('Foorball day: ' + str(self.numFootballDay))
                    self.quiniScraper.getFootballDay(self.numFootballDay)
                    matches = self.quiniScraper.getMatches()
                    self.sheetsOp.fillResults(matches, self.sheetTitle)
                    waitTime = config['periodCompleted']

            # FINISHED QUINIELA
            if currSt == State.FINISHED:
                self.numFootballDay, self.sheetId = self.sheetsOp.checkBornFootballDay()
                if self.numFootballDay:
                    print('FINISHED - New Football day detected!')
                    currSt = State.NEW
                    self.newInState = True
                else:
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


