from __future__ import print_function
import httplib2
import os
import codecs
import re

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
        self.people = []

        # Read people to play
        f = codecs.open(people, 'r', encoding='utf8')
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


    def checkBornFootballDay(self):
        """Determines if people have created a new sheet to be filled
        in case some it's found, it returns the number of football day
        :returns: football day number or None, sheetId
                  None,None in case of no new football day

        """
        newFootballDay = None
        sheetId = None
        result = self.service.spreadsheets().get(
                spreadsheetId=self.spreadsheetId).execute()
        sheets = result.get("sheets", [])
        
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


    def fillDoubles(self, sheetName, numDoubles):
        """Fills the doubles of a completed football day

        :sheetName: name of the sheet
        :numDoubles: obtains the number of doubles
        :returns: None

        """
        
        freqs = self.valuesGetRange(sheetName + "!O1:Q14", "ROWS")
        difs = []

        # Obtain freqs differences
        for matchFreqs in freqs:
            bigMax = max(range(len(matchFreqs)),
                    key=lambda i: matchFreqs[i])[0]
            bigVal = matchFreqs[bigMax]
            del matchFreqs[bigMax]
            lowMax = max(range(len(matchFreqs)),
                    key=lambda i: matchFreqs[i])[0]
            lowVal = matchFreqs[lowMax]

            difs.append(abs(bigVal - lowVal))

        # Obtain the double matches
        doubleMatches = []
        doubleResults = []
        for i in range(7):
            lowDifIndex = min(range(len(difs)),
                    key=lambda i: difs[i])[0]

            doubleMatches.append(lowDifIndex)
            del difs[lowDifIndex]


        # Fill resulting double columns
        doubleCol = []
        for i in range(len(difs)):
            result = ''

            if i in doubleMatches:
                result = max(range(len(difs[lowDifIndex])),
                        key=lambda i: difs[lowDifIndex][i])[0]
            if result == 0:
                result = '1'
            elif result == 1:
                result = 'X'
            elif result == 2:
                result = '2'
            else:
                result = ""

            doubleCol.append(result)

        
        # Write column in the sheet
        self.service.valuesUpdate(result, sheetTitle + "!R1:R14")



if __name__ == '__main__':
    sheetsOp = SheetsOperator('client_secret.json', '.credentials', '1s8zR4sYi4avM6q9N6qUUz3nEIlNWTOjTdCudfaudWV8', 559840847, 'quinielas-uc3m', 'people.txt')
    sheetsOp.startService()

    # sheetsOp.createFootballDay(1000)

    # cols = sheetsOp.colsFilled('Jornada 24')
    # print(cols)

    # num, id_ = sheetsOp.checkBornFootballDay()
    # print(str(num))
    # print(id_)

    # sheetsOp.deleteSheet(135049881)
    

