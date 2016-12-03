from QuinielaScraper import QuinielaScraper
from SheetsOperator import SheetsOperator
from SheetsOperator import SheetsOperator
from QuinielaScraper import QuinielaScraper
import os
import json
import time
import re


########################
### GLOBAL VARIABLES ###
########################
quiniScraper   = None
sheetsOp       = None
sheetId        = None
sheetTitle     = None
numDoubles     = None
newInState     = True



class State:
    NEW        = 1
    COMPLETED  = 2
    FINISHED   = 3


def enterNew():
    """Do the operations needed when a new football day is created
    :returns: None

    """
    # Set scraper for new day, and get matches
    numFootballDay = re.search("^Jornada (\d+)", sheetTitle)
    numFootballDay = int(numFootballDay.group(1))
    quiniScraper.getFootballDay(numFootballDay)
    matches = quiniScrapper.getMatches()

    # Get football matches in sheets format
    sheetMatches = []
    for match in matches:
        sheetMatches.append([match['local'], match['visiting']])

    # Fill matches
    sheetsOp.fillMatches(sheetMatches, sheetTitle)


def getCurrState():
    """Determines what is the current state in the quinielas spreadsheet
    :returns: State

    """
    # New sheet created for a football Day
    numFootballDay, sheetId = sheetsOp.checkBornFootballDay()
    if numFootballDay:
        newInState = True
        return State.NEW
    # No new football day created
    else:
        sheetId, sheetTitle = sheetOp.getLastFootballDay()
        if not sheetsOp.colsFilled():
            newInState = False
            return State.NEW

        # People completed columns
        if not sheetsOp.footballDayFinished(sheetTitle):
            # Doubles column not filled
            if not sheetsOp.DoublesFilled(sheetTitle, numDoubles):
                newInState = True
            return State.COMPLETED
        else:
            return State.FINISHED

    


def loop():
    """Executes the main loop of the daemon
    :returns: None

    """
    
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
    print('Getting current state')
    currSt = getCurrState()

    
    ###############
    ## MAIN LOOP ##
    ###############
    while True:
        waitTime = 0

        # NEW QUINIELA
        if currSt == State.NEW:
            if newInState:
                enterNew()
                newInState = False
            elif sheetsOp.colsFilled(sheetTitle):
                currSt = State.COMPLETED
                newInState = True
            else:
                waitTime = config['periodNew']

        # COMPLETED QUINIELA
        if currSt == State.COMPLETED:
            if newInState:
                sheetsOp.fillDoubles(sheetTitle, numDoubles)
                newInState = False
            elif sheetsOp.footballDayFinished(sheetTitle):
                currSt = State.FINISHED
                newInState = True
            else:
                waitTime = config['periodFinished']

        # FINISHED QUINIELA
        if currST == State.FINISHED:
            numFootballDay, sheetId = sheetsOp.checkBornFootballDay()
            if numFootballDay:
                currSt = State.NEW
                newInState = True
            else:
                waitTime = config['periodFinished']

        time.sleep(waitTime)



if __name__ == '__main__':
    loop()


