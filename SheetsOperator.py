from __future__ import print_function
import httplib2
import os
import codecs

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


if __name__ == '__main__':
    sheetsOp = SheetsOperator('client_secret.json', '.credentials', '1s8zR4sYi4avM6q9N6qUUz3nEIlNWTOjTdCudfaudWV8', 559840847, 'quinielas-uc3m', 'people.txt')
    sheetsOp.startService()

    # sheetsOp.createFootballDay(1000)

    cols = sheetsOp.colsFilled('Jornada 24')
    print(cols)
    

