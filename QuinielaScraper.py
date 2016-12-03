from bs4 import BeautifulSoup
import requests

class QuinielaScraper:
    """Web scrapper to get quiniela results """


    def __init__(self, season):
        """Creates the scraper

        :season: '2016_2017'

        """
        self.season = season
        self.url = 'http://resultados.as.com/quiniela'
        self.lastDay = None
        self.matches = None
        self.scraper = None
        self.currDay = None
        pass


    def getMatch(self, x):
        """Obtains the result of x match.

        :x: number of match to get
        :returns: '1', 'x', '2'

        """
        return self.matches[x]['result']


    def getMatches(self):
        """Obtains the lastDay matches.
        :returns: {[
                'local': R. Madrid,
                'visiting': Valencia,
                'result': x
            ], ...}

        """
        return self.matches


    def parsePleno15(self):
        """Obtains the pleno al 15 match
        :returns: {
                'local': R. Madrid,
                'visiting': Barcelona,
                'result': '0--M'
                }

        """
        matchLoc = self.scraper.select('table.pleno-15 tr')[1]
        nameLoc = matchLoc.select('td.enfrentamientos')[0].a.span.text
        resulLoc = matchLoc.select('td.quini')[0].select('span.signo-def')

        matchVis = self.scraper.select('table.pleno-15 tr')[2]
        nameVis = matchVis.select('td.enfrentamientos')[0].a.span.text
        resulVis = matchVis.select('td.quini')[0].select('span.signo-def')

        resul = ''
        if resulLoc:
            resul = resulLoc[0].text + '--' + resulVis[0].text

        return {'local': nameLoc,
                'visiting': nameVis,
                'result': resul}


    def parseMatch(self, x):
        """Obtains the match x within the parser

        :x: number of the match
        :returns: {
                'local': R. Madrid,
                'visiting': Valencia,
                'result': 'x' or '0--M'
                }

        """
        # Check if requested is pleno al 15
        if x==15:
            return self.parsePleno15()

        match = self.scraper.select('table.tabla-quiniela tr')[x]
        result = match.select('td.quini')[0].select('span.signo-def')
        if not result:
            result = ''
        else:
            result = result[0].text

        return {'local': match.select('td')[1].a.span.text,
                'visiting': match.select('td')[2].a.span.text,
                'result': result}


    def getFootballDay(self, footballDay):
        """Gets matches of footballDay and stores it in the scraper

        :footballDay: number of football day
        :returns: None

        """
        self.currDay = footballDay
        asQuiniela = requests.get(self.url + '/' + self.season +
                '/jornada_' + str(footballDay))
        asQuiniela = asQuiniela.text
        self.scraper = BeautifulSoup(asQuiniela, "lxml")


        # Add all matches
        self.matches = []
        for i in range(15):
            partido = self.parseMatch(i+1)
            self.matches.append(partido)


if __name__ == '__main__':
    as_ = QuinielaScraper('2016_2017')
    as_.getFootballDay(22)
    matches = as_.getMatches()



