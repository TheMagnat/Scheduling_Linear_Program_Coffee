from pulp import LpStatus

from reader import readFile
from helper import convert2dWeekDayAndHours
from visu import visualize
from weekLP import WeekLP, WeekData

import numpy as np

from itertools import chain, combinations

### Param
maxExecutionTime = 120
rushOneMore = False
allowOneMoreHalfHour = True

formationStopHourIndex = 6 #Ils arrêtent la formation à 11h30


dayToIndex = {"Lundi":0, "Mardi":1, "Mercredi":2, "Jeudi":3, "Vendredi":4, "Samedi": 5}

#Nombre d'employee minimum par demi heure
#  0    1    2     3     4     5     6     7     8     9     10   11    12     13    14   15    16
hoursToIndex = {"8h30":0, "9h":1, "9h30":2, "10h":3, "10h30":4, "11h":5, "11h30":6, "12h":7,
                "12h30":8, "13h":9, "13h30":10, "14h":11, "14h30":12, "15h":13, "15h30":14,
                "16h":15, "16h30":16, "17h":17, "17h30":18, "18h":19, "18h30":20, "19h":21, "19h30":22}

minimumPplCre          = [1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2]
minimumPplCreMonday    = [0, 0, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0]
minimumPplCreFormation = [1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2]
# 8h30 11h30

rushStartIndex = 7
rushEndIndex = 12




if rushOneMore:
    for i in range(rushStartIndex, rushEndIndex):
        minimumPplCre[i] += 1
        minimumPplCreMonday[i] += 1
        minimumPplCreFormation[i] += 1
        
print(minimumPplCre)
print(minimumPplCreMonday)
print(minimumPplCreFormation)

pplName, pplWeekHours, maxHalfHoursPerDay, inFormation, startHour, fullEndBefore, fullAbsentRange = readFile("input.xlsx")

# pplName = ["Chloé", "Maeva", "Johanne", "Alexis", "Thomas", "Line", "Philippine"]
# pplWeekHours = [20, 25, 20, 20, 24, 25, 20] #Heures que dois faire un employee par semaine
# maxHalfHoursPerDay = [9, 11, 9, 9, 11, 11, 9] # Temps maximum pendant lequel un employee peut rester
# maxHalfHoursPerDay = [9 if hour <= 20 else 11 for hour in pplWeekHours]

if allowOneMoreHalfHour:
    for i, time in enumerate(maxHalfHoursPerDay):
        maxHalfHoursPerDay[i] += 1

print(maxHalfHoursPerDay)

# inFormation = [True, False, True, True, True, True, True]

#On retire le temps de formation de leurs temps de travail
for i, isInFormation in enumerate(inFormation):
    if isInFormation:
        # -1 car ils ont une demi heure de pause pendant la formation
        pplWeekHours[i] -= (formationStopHourIndex - 1) / 2


#Pour forcer une personne à arriver plus tard
# startHour = [0, 0, 0, 0, 0, 7, 0]

#Pour forcer un employee à commencer n fois pendant la semaine
# forceEmployeeNbStart = False
# nbStartRequired = [0, 0, 0, 0, 0, 0, 0]


#Pour forcer un employee à avoir son lundi ou son samedi
# forceSundayBreak = True
# shouldForceSunday = [False, False, False, False, False, False, False]


#Pour indiquer la non presence d'une personne à parti/jusqu'a une certaine heure
activateRestrictions = False
# endBefore = [[], [], [], [], [], [], [["Mardi", "18h30"]]]
# endBefore = convert2dDayAndHours(endBefore, dayToIndex, hoursToIndex)

# absentRange = [[], [["Lundi", "10h30", "14h30"]], [], [], [["Lundi", "14h", "16h30"], ["Samedi", "14h", "16h30"]], [], []]
# absentRange = convert2dDayAndHours(absentRange, dayToIndex, hoursToIndex)

# currentWeek = 1

#To generate the restriction for the current week
# if activateRestrictions:
def generateRestrictions(currentWeek):
    endBefore = []
    absentRange = []
    for i, pplEndRestrictions in enumerate(fullEndBefore):
        endBefore.append([])
        for endRestriction in pplEndRestrictions:
            if endRestriction[0] == currentWeek:
                endBefore[-1].append(endRestriction[1:])
    
    for i, pplRangeRestrictions in enumerate(fullAbsentRange):
        absentRange.append([])
        for rangeRestriction in pplRangeRestrictions:
            if rangeRestriction[0] == currentWeek:
                absentRange[-1].append(rangeRestriction[1:])

    return endBefore, absentRange

# print(fullEndBefore)
# print(fullAbsentRange)

# print(endBefore)
# print(absentRange)
# exit(0)


# ["Chloé", "Maeva", "Johanne", "Alexis", "Thomas", "Line", "Philippine"]
forceEarly = True
needStartEarly = [False, False, False, False, False, False, False]

forceLate = True
needStartLate = [False, False, False, False, False, False, False]

# print(endBefore)
# print(absentRange)

# exit(0)

n = len(pplWeekHours) #Nb Employee
o = len(minimumPplCre) #Nb demi-heures

""" Questions
Quoi le plus chiant entre une journée de 6h/5h ou Quelqu'un qui vient pas longtemps

Pouvoir forcer un samedi ou lundi de congé
Pouvoir forcer des impossibilités de travailler tel jour


OK - jusqua 16h30 on peut mettre 1
OK - Ne pas arriver au millieux de service (avant midi)

OK - Si une coupure le mercredi, retirer les 30min de pause

OK - Chloé ou Maeva au moins là pour Midi

OK - Line pas les matins (10h mini)
TODO: le minimiser plutot que l'interdire ?

A du mal à enchainer : Chloé



OK - On peut relacher le midi à 2 employées

Binome: Thomas Joanne
        Alexis Philipine
        Chloé et Maeva
        
OK - ceux à 20h seulement 4h
OK - exeptionnellement 6h

OK - 1 jour de congé par semaine,
OK - favoriser de le coller au dimanche
"""
nbWeeks = 4


class WeekIterationInformation:

    def __init__(self, doneSundays):
        self.doneSundays = doneSundays

    def generateNextForcedSundaysSubset(self):
        
        missingSundays = []
        for i, nbSundays in enumerate(self.doneSundays):
            if nbSundays == 0:
                missingSundays.append(i)

        if len(missingSundays) == 0:
            self.sundaysSubset = [[]]
            return

        self.sundaysSubset = [list(elem) for elem in chain.from_iterable(list(combinations(missingSundays, r)) for r in range(len(missingSundays)+1))]

    def storeLP(self, lp):
        self.lp = lp


def generateForceSundayArray(pplToForceSunday, n):
    forceSunday = [False] * n
    for ppl in pplToForceSunday:
        forceSunday[ppl] = True
    return forceSunday

weekData = WeekData(minimumPplCre, minimumPplCreMonday, minimumPplCreFormation)

n = len(pplName) #Nb Employee
doneSundays = np.zeros(n, dtype=int)
weeksInfo = [WeekIterationInformation(doneSundays)]
# forceSunday = [False] * n

#We prepare first week info
weeksInfo[0].sundaysSubset = [[]]

currentWeek = 0
success = False


while True:

    status = 0
    while status != 1 and weeksInfo[-1].sundaysSubset:

        pplToForceSunday = weeksInfo[-1].sundaysSubset.pop()
        #TODO: Ne plus regarder ceux qui sont à 0, mais qui sont a la valeur minimale de l'array
        forceSunday = generateForceSundayArray(pplToForceSunday, n)

        endBefore, absentRange = generateRestrictions(currentWeek)

        # Create the model
        lp = WeekLP()
        lp.generate(weekData, pplWeekHours, maxHalfHoursPerDay, inFormation, startHour, endBefore, absentRange, forceSunday, needStartEarly, needStartLate)


        status, objectiveValue = lp.solve()

        print(f"status: {status}, {LpStatus[status]}")
        print(f"objective: {objectiveValue}")

        lp.printObjectives()

    if not status:
        print("Could not find a solution...")

        currentWeek -= 1
        weeksInfo.pop()

        if not weeksInfo:
            success = False
            break
        
        doneSundays -= weeksInfo[-1].lp.getSundays()
        weeksInfo[-1].lp = None

        continue

    #We store the LP
    weeksInfo[-1].storeLP(lp)

    #We update the number of sundays done
    doneSundays += weeksInfo[-1].lp.getSundays()

    print("Accepted LP !")
    print("Sundays:", weeksInfo[-1].lp.getSundays(), "done sundays:", doneSundays)
    # print("Starting: ", weeksInfo[-1].getStarting())

    currentWeek += 1
    if currentWeek >= nbWeeks:
        success = True
        break

    #We generate the next week iteration information
    weeksInfo.append( WeekIterationInformation(doneSundays) )

    #We generate the next subset of sundays to force
    weeksInfo[-1].generateNextForcedSundaysSubset()
    # weekAccepted = True

if not success:
    print("Failed to find a solution. Please try with a greater time limit.")

else:
    for info in weeksInfo:
        info.lp.printObjectives()
        employeeHours = info.lp.getScheduling()
        print(employeeHours)

        visualize(employeeHours, pplName)