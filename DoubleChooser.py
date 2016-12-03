import random
import copy
import Utils_

class DoubleChooser():

    """Class to select the doubles of a football day"""

    def __init__(self, freqs, modes, participants, numDoubles):
        """
        :freqs: list with the frequencies of a match
        :modes: modes for each match
        :participants: number of participants in quiniela
        :numDoubles: number of doubles in quiniela

        """
        self.freqs = freqs
        self.modes = modes
        self.participants = participants
        self.numDoubles = numDoubles
        

    def chooseRandomEls(self, arr, n):
        """Chooses `n` random elements of `arr`

        :arr: list of elements
        :n: number of elements
        :returns: list with random elements

        """

        randomEls = []
        i = 0
        while i < n:
            num = random.randint(0, len(arr)-1)
            randomEls.append(arr[num])
            del arr[num]
            i += 1

        return randomEls


    def orderDifs(self, difs, difsPos):
        """Orders the differences values and the positions

        :difs: frequency differences
        :difsPos: positions of the diferences
        :returns:
          :difs_: reordered difs
          :difsPos_: reordered difs positions
          :difsCounts: {
            0: #of_differences_with_zero,
            1: #of_differences_with_zero,
            ...
          }

        """
        difs_ = []
        difsPos_ = []
        difsCounts = dict()

        for dif in range(self.participants+1):
            i = 0
            counts = 0
            while i < len(difs):
                if difs[i] == dif:
                    difs_.append(difs[i])
                    difsPos_.append(difsPos[i])
                    counts += 1
                i += 1
            difsCounts[dif] = counts

        return difs_, difsPos_, difsCounts


    def chooseDoubleRows(self, difs, difsPos, difsCount):
        """Chooses the rows that will be chosen to select a double

        :difs: ordered freq differences (ascendant)
        :difsPos: row positions of each entry at difs
        :difsCount: {0: #of_0_diff_rows, ...}
        :returns: array with indexes of rows chosen

        """
        
        chosenDoubles = []
        dif = 0
        currIdx = 0

        while len(chosenDoubles) < self.numDoubles:
            # If remains less than rows with dif -> choose randomly
            if difsCount[dif] > self.numDoubles - len(chosenDoubles):
                randEls = self.chooseRandomEls(
                        difsPos[currIdx:currIdx+difsCount[dif]-1],
                        self.numDoubles - len(chosenDoubles))
                chosenDoubles.extend(randEls)
            # Append all values of curr diff
            else:
                i = 0
                while i < difsCount[dif]:
                    chosenDoubles.append(difsPos[currIdx+i])
                    i += 1
                currIdx += i
            dif += 1

        return chosenDoubles



    def getDoubleCol(self, doubles):
        """Obtains the columns of doubles to be put

        :doubles: list with doubles indexes
        :returns: list with the column of doubles, e.g, ['X','','','1', ... ]

        """
        # Fill resulting double columns
        doubleCol = []
        for row in range(14):
            secondMax = ''
            
            # Check if row is among doubles
            if row in doubles:
                selected = self.modes[row]
                if selected == 0:
                    selected = 1
                elif selected == 1:
                    selected = 0

                freqsCandidate = self.freqs[row]
                freqsCandidate[selected] = -1
                _, secondMax = Utils_.maximo(freqsCandidate)

            # Translate secondMax to a value
            if secondMax == 0:
                secondMax = '1'
            elif secondMax == 1:
                secondMax = 'X'
            elif secondMax == 2:
                secondMax = '2'

            doubleCol.append(secondMax)

        return doubleCol
    


    def tellDoubles(self):
        """Tells the doubles associated to the freqs

        :returns: list for the column of doubles, e.g:
                  ['X', '', '', '1', '2', ... ]

        """
        
        difs = []
        difsPos = []

        freqs_ = copy.deepcopy(self.freqs)

        # Obtain freqs differences
        i = 0
        for matchFreqs in freqs_:
            bigVal, bigPos = Utils_.maximo(matchFreqs)
            del matchFreqs[bigPos]
            lowVal, lowPos = Utils_.maximo(matchFreqs)

            difs.append(abs(bigVal - lowVal))
            difsPos.append(i)
            i += 1

        # Order the differences    
        difs_, difsPos_, difsCounts = self.orderDifs(difs, difsPos)

        # Select the double rows
        doubleRows = self.chooseDoubleRows(difs_, difsPos_, difsCounts)

        # Get columns of doubles
        doubleCol = self.getDoubleCol(doubleRows)

        return doubleCol



if __name__ == '__main__':

    # Testing

    freqs = [
    [0,2,4],
    [3,2,1],
    [4,2,0],
    [2,4,0],
    [6,0,0],
    [3,1,2],
    [4,1,1],
    [2,1,3],
    [6,0,0],
    [6,0,0],
    [3,2,1],
    [5,1,0],
    [4,1,1],
    [6,0,0]
    ]

    mode = [
    2,
    1,
    1,
    0,
    1,
    1,
    1,
    2,
    1,
    1,
    1,
    1,
    1,
    1
    ]

    doubleChooser = DoubleChooser(freqs, mode, 6, 7)
    doubles = doubleChooser.tellDoubles()

    print(doubles)


