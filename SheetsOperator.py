from __future__ import print_function
import httplib2
import os
import codecs
import re
import Utils_

from DoubleChooser import DoubleChooser

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage



class SheetsOperator():
    """Class with operations for google sheets"""

    def __init__(self, secretFile, credentials, spreadSheetId, plantillaId,
            appName, people):
        """Inits a SheetsOperator
        :secretFile: secretFile path
        :credentials: credentials folder path
        :spreadsheetId: ID of the Google spreadsheet
        :plantillaId: ID of the `plantilla` sheet
        :appName: application name
        :people: TXT file with the people playing this footballDay, this file
                 should have a person name in each line
        """
        self.secretFile = secretFile
        self.credentials = credentials
        self.spreadsheetId = spreadSheetId
        self.plantillaId = plantillaId
        self.service = None
        self.appName = appName
        self.peopleF = people
        self.people = []

        self.readPeople()


        

    def readPeople(self):
        """Reads the people names in the file and store them in class
        :returns: None

        """
        self.people = []

        f = codecs.open(self.peopleF, 'r', encoding='utf8')
        line = f.readline()
        while line:
            self.people.append(line[0:-1])
            line = f.readline()


    def startService(self):
        """Starts the Google sheets API service
        :returns: None

        """
        
        # Get credentials
        credential_dir = self.credentials
        if not os.path.exists(credential_dir):
            os.makedirs(credential_dir)
        credential_path = os.path.join(credential_dir,
                                   'sheets.googleapis.com-python-quickstart.json')

        store = Storage(credential_path)
        credentials = store.get()
        if not credentials or credentials.invalid:
            flow = client.flow_from_clientsecrets(self.secretFile, 'https://www.googleapis.com/auth/spreadsheets')
            flow.user_agent = self.appName
            credentials = tools.run_flow(flow, store)
            print('Storing credentials to ' + credential_path)

        
        # Get service
        http = credentials.authorize(httplib2.Http())
        discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                        'version=v4')
        self.service = discovery.build('sheets', 'v4', http=http,
                                  discoveryServiceUrl=discoveryUrl)


    def deleteSheet(self, sheetId):
        """Deletes a sheet with given sheetId

        :sheetId: ID of the sheet to delete
        :returns: None

        """
        body = {
            "requests": [{
                "deleteSheet": {
                    "sheetId": sheetId
                }
            }]
        }
        self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.spreadsheetId, body=body).execute()


    def getSheets(self):
        """Obtains the sheets of current spreadsheet
        :returns: [
            {"properties": {
                "title": --,
                "sheetId": --,
                ...
            }},
            ...
            ]

        """
        result = self.service.spreadsheets().get(
                spreadsheetId=self.spreadsheetId).execute()
        sheets = result.get("sheets", [])

        return sheets

    def checkBornFootballDay(self):
        """Determines if people have created a new sheet to be filled
        in case some it's found, it returns the number of football day
        :returns: football day number or None, sheetId
                  None,None in case of no new football day

        """
        newFootballDay = None
        sheetId = None
        sheets = self.getSheets()
        
        i = 0
        while not newFootballDay and i < len(sheets):
            sheet = sheets[i]
            title = sheet['properties']['title']
            footballDay = re.search('^\d+$', title)
            if footballDay:
                newFootballDay = int(title)
                sheetId = sheet['properties']['sheetId']
            i += 1
    
        return newFootballDay, sheetId

    
    def getLastFootballDay(self):
        """Obtains the sheet associated to the last football day
        :returns: number(sheetId), sheetTitle

        """
        sheets = self.getSheets()
        footballDays = []
        sheetPos = []

        # Push football day numbers
        i = 0
        for sheet in sheets:
            title = sheet['properties']['title']
            match = re.search("^Jornada (\d+)$", title)
            if match:
                footballDays.append(int(match.group(1)))
                sheetPos.append(i)
            i += 1

        
        # Find biggest football day number
        _, idx = Utils_.maximo(footballDays)
        sheetId = sheets[sheetPos[idx]]['properties']['sheetId']
        sheetTitle = sheets[sheetPos[idx]]['properties']['title']

        return sheetId, sheetTitle
        

    def createFootballDay(self, footballDay):
        """Creates a football day sheet

        :footballDay: number of football day
        :returns: ID of the football day sheet

        """
        
        # Copy plantilla
        body = {
            "destinationSpreadsheetId": self.spreadsheetId,
        }
        result = self.service.spreadsheets().sheets().copyTo(spreadsheetId=self.spreadsheetId, sheetId=self.plantillaId, body=body).execute()
        createdSheetId = result.get('sheetId', [])


        # Rename plantilla to Jornada Y
        title = "Jornada " + str(footballDay)
        body = {
            "requests": [
            {
                "updateSheetProperties": {
                    "properties":
                    {
                        "sheetId": createdSheetId,
                        "title": title
                    },
                    "fields": "title"
                }
            }
          ],
          "includeSpreadsheetInResponse": True,
          "responseIncludeGridData": True,
        }
        result = self.service.spreadsheets().batchUpdate(spreadsheetId=self.spreadsheetId, body=body).execute()
        updatedSheet = result.get('replies', [])
        # createdSheetName = updatedSheet['addSheet']['properties']['title']

        return createdSheetId, title


    def footballDayFinished(self, sheetTitle):
        """Checks if the football day in `sheetTitle` has finished

        :sheetTitle: title of the football day sheet
        :returns: boolean

        """
        results = self.valuesGetRange(sheetTitle + "!E1:E15", "COLUMNS")

        # Empty -> no completed match
        if not results:
            return False

        results = results[0]
        # Not all matches finished
        if len(results) < 15:
            return False

        return True


    def valuesUpdate(self, values, range_):
        """Updates a batch of values in a given range

        :values: range of values to update
        :range: range to be updated
        :returns: the result of the request

        """
        bodyUp = {
            'valueInputOption': "USER_ENTERED",
            'data': [
                {
                    'range': range_,
                    'values': values
                }
            ]
        }

        result = self.service.spreadsheets().values().batchUpdate(spreadsheetId=self.spreadsheetId, body=bodyUp).execute()

        return result


    def valuesGetRange(self, range_, mode):
        """Obtains the values in a range_
        the range of values will be provided in `mode` order
        ROW order - A1:B2 - [[A1,A2],[B1,B2]]
        COLUMNS order - A1:B2 - [[A1,B1],[A2,B2]]

        :range_: range of values to obtain
        :mode: 'ROW' or 'COLUMNS'
        :returns: matrix with values in row order

        """

        result = self.service.spreadsheets().values().get(spreadsheetId=self.spreadsheetId, range=range_, majorDimension=mode).execute()
        return result.get('values', [])
        

    def colsFilled(self, sheetName):
        """Checks if all the people have filled their columns
        :sheetName: name of the sheet to get values from
        :returns: boolean

        """


        self.readPeople() # Refresh who's playing
        print('people')
        print(self.people)
        range_ = sheetName + "!F1:M16"
        peopleCols = self.valuesGetRange(range_, 'COLUMNS')
        allFilled = True
        i = 0
        while allFilled and i < len(peopleCols):
            personCol = peopleCols[i]
            person = personCol[15]
            if person in self.people:
                pMatches = personCol[0:-1]
                allFilled = allFilled and reduce(
                        lambda x,y: x!=u'' and y!=u'',
                        pMatches)
            i += 1
        
        return allFilled

    def fillMatches(self, matches, sheetTitle):
        """Fills a new sheet with the football matches

        :matches: [
            {
                'local': 'Madrid',
                'visiting': 'Valencia',
                'result': ___
            },
            ...
        ]
        :sheetTitle: title name of sheet
        :returns: None

        """
        
        matchRows = []
        for match in matches:
            matchRows.append([match['local'], match['visiting']])

        range_ = sheetTitle + "!A1:B15"
        self.valuesUpdate(matchRows, range_)


    def fillResults(self, matches, sheetTitle):
        """Fill the results of the football day under the sheet `sheetTitle`

        :matches: [
            {
                'local': 'Madrid',
                'visiting': 'Valencia',
                'result': ___
            },
            ...
        ]
        :sheetTitle: title name of the sheet
        :returns: None

        """
        results = []
        for match in matches:
            results.append([match['result']])

        range_ = sheetTitle + "!E1:E15"
        self.valuesUpdate(results, range_)


    def doublesFilled(self, sheetTitle, numDoubles):
        """Checks if the doubles column is filled in the football day
           associated to the sheet with name `sheetTitle`

        :sheetTitle: title of the sheet
        :numDoubles: number of doubles to be filled
        :returns: boolean

        """
        doubles = self.valuesGetRange(sheetTitle + "!R1:R14", "COLUMNS")
        if not doubles:
            return False
        doubles = doubles[0]
        filledDoubles = 0
        for double in doubles:
            filledDoubles += 1 if double != u'' else 0

        return filledDoubles == numDoubles


    def fillDoubles(self, sheetName, numDoubles):
        """Fills the doubles of a completed football day

        :sheetName: name of the sheet
        :numDoubles: obtains the number of doubles
        :returns: None

        """
        
        freqs = self.valuesGetRange(sheetName + "!O1:Q14", "ROWS")
        modes = self.valuesGetRange(sheetName + "!N1:N14", "COLUMNS")
        modes = modes[0]

        # Convert values to integers
        freqsInt = []
        modesInt = [int(mode) for mode in modes]
        for freqs_ in freqs:
            row = []
            for freq in freqs_:
                row.append(int(freq))
            freqsInt.append(row)

        # Obtain the doubles
        doubleChooser = DoubleChooser(freqsInt, modesInt,
                len(self.people), numDoubles)
        doubles = doubleChooser.tellDoubles()

        # Encapsulate each value in a list
        doubles_ = []
        for double in doubles:
            doubles_.append([double])
        self.valuesUpdate(doubles_, sheetName + "!R1:R14")



if __name__ == '__main__':
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


    # print(sheetsOp.doublesFilled('plantilla', 7))

    # sheetsOp.fillDoubles('Hoja 18', 7)

    # id_, lastDay = sheetsOp.getLastFootballDay()
    # print("Last day: " + lastDay + " - id: " + str(id_))

    # print(sheetsOp.footballDayFinished('Jornada 22'))

    # sheetsOp.createFootballDay(1000)

    # cols = sheetsOp.colsFilled('Jornada 24')
    # print(cols)

    # num, id_ = sheetsOp.checkBornFootballDay()
    # print(str(num))
    # print(id_)

    # sheetsOp.deleteSheet(135049881)
    

