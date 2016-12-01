from __future__ import print_function
import httplib2
import os

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage



class SheetsOperator():
    """Class with operations for google sheets"""

    def __init__(self, secretFile, credentials, spreadSheetId, plantillaId,
            appName):
        """Inits a SheetsOperator
        :secretFile: secretFile path
        :credentials: credentials folder path
        :spreadsheetId: ID of the Google spreadsheet
        :plantillaId: ID of the `plantilla` sheet
        :appName: application name
        """
        self.secretFile = secretFile
        self.credentials = credentials
        self.spreadsheetId = spreadSheetId
        self.plantillaId = plantillaId
        self.service = None
        self.appName = appName


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
        bodyUp = {
            'valueInputOption': "USER_ENTERED",
            'data': [
                {
                    'range': range_,
                    'values': matchRows
                }
            ]
        }

        result = self.service.spreadsheets().values().batchUpdate(spreadsheetId=self.spreadsheetId, body=bodyUp).execute()


if __name__ == '__main__':
    sheetsOp = SheetsOperator('client_secret.json', '.credentials', '1s8zR4sYi4avM6q9N6qUUz3nEIlNWTOjTdCudfaudWV8', 559840847, 'quinielas-uc3m')
    sheetsOp.startService()

    sheetsOp.createFootballDay(1000)

    
    sheetsOp.fillMatches([{'local': 'A', 'visiting': 'B'},
        {'local': 'A', 'visiting': 'B'},
        {'local': 'A', 'visiting': 'B'},
        {'local': 'A', 'visiting': 'B'},
        {'local': 'A', 'visiting': 'B'},
        {'local': 'A', 'visiting': 'B'},
        {'local': 'A', 'visiting': 'B'},
        {'local': 'A', 'visiting': 'B'},
        {'local': 'A', 'visiting': 'B'},
        {'local': 'A', 'visiting': 'B'},
        {'local': 'A', 'visiting': 'B'},
        {'local': 'A', 'visiting': 'B'},
        {'local': 'A', 'visiting': 'B'},
        {'local': 'A', 'visiting': 'B'},
        {'local': 'A', 'visiting': 'B'}
        ], 'Jornada 1000')


