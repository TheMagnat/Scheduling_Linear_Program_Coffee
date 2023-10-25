
from pulp import LpMinimize, LpMaximize, LpProblem, LpStatus, lpSum, LpVariable, LpBinary, LpInteger, LpContinuous, LpConstraint, LpAffineExpression, PULP_CBC_CMD

from reader import readFile
from helper import convert2dDayAndHours
from visu import visualize

### Param
maxExecutionTime = 680
rushOneMore = False
allowOneMoreHalfHour = True
favoriseBreakNearSunday = True
repartir = True

#Data of the problem
nbWeek = 1 #Nb semaines
m = 6 #Nb jours

#+1 pour la pause de 30min
maxHalfHour = 5*2 + 1 #5 hours
minHalfHourIfWorking = 2*2 + 1 #5 hours


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
rushNbOpti = 3

earlyEnd = 7

rushStartIndex = 7
rushEndIndex = 12

reduceFormationDay = True
formationReduceStart = 16
formationReduceEnd = 21

nbHalfHourToPause = 4 * 2 #4h de travail = une pause

if rushOneMore:
    for i in range(rushStartIndex, rushEndIndex):
        minimumPplCre[i] += 1
        minimumPplCreMonday[i] += 1
        minimumPplCreFormation[i] += 1
        
print(minimumPplCre)
print(minimumPplCreMonday)
print(minimumPplCreFormation)

pplName, pplWeekHours, maxHalfHoursPerDay, inFormation, startHour, shoudlForceSunday, needStartEarly, needStartLate, endBefore, absentRange = readFile("input.xlsx")

# pplName = ["Chloé", "Maeva", "Johanne", "Alexis", "Thomas", "Line", "Philippine"]
# pplWeekHours = [20, 25, 20, 20, 24, 25, 20] #Heures que dois faire un employee par semaine
# maxHalfHoursPerDay = [9, 11, 9, 9, 11, 11, 9] # Temps maximum pendant lequel un employee peut rester
# maxHalfHoursPerDay = [9 if hour <= 20 else 11 for hour in pplWeekHours]

if allowOneMoreHalfHour:
    for i, time in enumerate(maxHalfHoursPerDay):
        maxHalfHoursPerDay[i] += 1

print(maxHalfHoursPerDay)

# inFormation = [True, False, True, True, True, True, True]
formationStopHourIndex = 6 #Ils arrêtent la formation à 11h30
formationDayIndex = 2

#On retire le temps de formation de leurs temps de travail
for i, isInFormation in enumerate(inFormation):
    if isInFormation:
        # -1 car ils ont une demi heure de pause pendant la formation
        pplWeekHours[i] -= (formationStopHourIndex - 1) / 2

#Equipier dont il faut au moins 1 le midi
forceAtLeastOne = False
atLeastOneIndex = [0, 1]

#Pour forcer une personne à arriver plus tard
allowLateStart = True
startHour = [0, 0, 0, 0, 0, 7, 0]

#Pour forcer un employee à commencer n fois pendant la semaine
#TODO: rendre ça par semaine
forceEmployeeNbStart = False
nbStartRequired = [0, 0, 0, 0, 0, 0, 0]

#Pour insiter l'algorithme à eviter de mettre ces paires ensemble
activateNegativePair = True
negativePairs = [[2, 4], [3, 6], [0, 1]]

#Pour forcer un employee à avoir son lundi ou son samedi
#TODO: faire ça par semaine et pas pour tout le mois
forceSundayBreak = False
# shoudlForceSunday = [False, False, False, False, False, False, False]


#TODO: Rendre ça par semaine
#Pour indiquer la non presence d'une personne à parti/jusqu'a une certaine heure
activateRestrictions = True
# endBefore = [[], [], [], [], [], [], [["Mardi", "18h30"]]]
# endBefore = convert2dDayAndHours(endBefore, dayToIndex, hoursToIndex)

# absentRange = [[], [["Lundi", "10h30", "14h30"]], [], [], [["Lundi", "14h", "16h30"], ["Samedi", "14h", "16h30"]], [], []]
# absentRange = convert2dDayAndHours(absentRange, dayToIndex, hoursToIndex)

forceSameStartDuringWeek = True

#TODO: Par semaine
# ["Chloé", "Maeva", "Johanne", "Alexis", "Thomas", "Line", "Philippine"]
# forceEarly = True
# needStartEarly = [True, False, False, False, False, False, False]

# forceLate = True
# needStartLate = [False, True, False, False, False, False, False]

print(endBefore)
print(absentRange)

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


# Create the model
model = LpProblem(name="Café", sense=LpMinimize)

# Create a dictionary to store the variables
x = LpVariable.dicts("x", (range(n), range(nbWeek), range(m), range(o)), cat=LpBinary)


#Chaque demi heure doit avoir au moins le nombre d'employee minimum de minimumPplCre
if repartir:
    maxEmployee = LpVariable("maxEmployee", lowBound=0, upBound=n, cat=LpContinuous)

#On doit respecter la charge à chaque demi heure de chaque jour de chaque semaine
respectedCharge = LpVariable.dicts("respectedCharge", (range(nbWeek), range(m), range(o)), lowBound=0, upBound=3, cat=LpContinuous)
for j in range(m):
    for k in range(o):
        for week in range(nbWeek):

            currentConstantList = []

            if j == 0:
                currentConstant = minimumPplCreMonday[k]
            elif j == formationDayIndex:
                currentConstant = minimumPplCreFormation[k]
            else:
                currentConstant = minimumPplCre[k]


            if currentConstant == 0:
                model += lpSum(x[i][week][j][k] for i in range(n)) == 0
            else:
                model += lpSum(x[i][week][j][k] for i in range(n)) >= currentConstant

                if repartir:
                    model += maxEmployee >= lpSum(x[i][week][j][k] for i in range(n)) - currentConstant
                # model += respectedCharge[j][k] >= currentConstant - lpSum(x[i][week][j][k] for i in range(n))


#On cree une variable pour indiquer le nombre de demi-heures que travail un employee par jour
dayHalfHours = LpVariable.dicts("dayHalfHours", (range(n), range(nbWeek), range(m)), lowBound=0, upBound=o, cat=LpInteger)
for i in range(n):
    for week in range(nbWeek):
        for j in range(m):
            model += dayHalfHours[i][week][j] == lpSum(x[i][week][j][k] for k in range(o))


if allowOneMoreHalfHour:
    sixHoursDay = LpVariable.dicts("sixHoursDay", (range(n), range(nbWeek), range(m)), cat=LpBinary)
    for i in range(n):
        for week in range(nbWeek):
            for j in range(m):
                #print( maxHalfHoursPerDay[i], maxHalfHoursPerDay[i] - 1)
                model += sixHoursDay[i][week][j] >= dayHalfHours[i][week][j] - (maxHalfHoursPerDay[i] - 1)


#On cree une variable pour indiquer si un employee prendra une pause ce jour
needPause = LpVariable.dicts("needPause", (range(n), range(nbWeek), range(m)), cat=LpBinary)
z = LpVariable.dicts("z", (range(n), range(nbWeek), range(m)), cat=LpBinary)
for i in range(n):
    for week in range(nbWeek):
        for j in range(m):

            # if j == formationDayIndex and inFormation[i]:
            #     model += needPause[i][week][j] == 0
            #     continue

            model += z[i][week][j] * nbHalfHourToPause >= nbHalfHourToPause - dayHalfHours[i][week][j]
            model += needPause[i][week][j] <= 1 - z[i][week][j]
            model += needPause[i][week][j] * o >= dayHalfHours[i][week][j] - (nbHalfHourToPause - 1)

            # model += needPause[i][j] * o >= dayHalfHours[i][j] - (nbHalfHourToPause - 1)
            # model += needPause[i][j] * nbHalfHourToPause <= dayHalfHours[i][j]


#On cree une variable pour indiquer si un employee travail le jour j ou non
#TODO: try with Z too
working = LpVariable.dicts("working", (range(n), range(nbWeek), range(m)), cat=LpBinary)
for i in range(n):
    for week in range(nbWeek):
        for j in range(m):
            model += working[i][week][j] * maxHalfHoursPerDay[i] >= dayHalfHours[i][week][j] #For working to be equal to 1 if dayHalfHours is equal to more than 1
            model += working[i][week][j] <= dayHalfHours[i][week][j] #Force working to be equal to 0 if dayHalfHours is equal to 0

#Variable représentant le nombre de jour travaille pour chaque equipier dans une semaine
# workingDayInWeek = LpVariable.dicts("workingDayInWeek", (range(n), range(nbWeek)), lowBound=0, upBound=6, cat=LpInteger)
# for i in range(n):
#     for week in range(nbWeek):
#         model += workingDayInWeek[i][week] == lpSum(working[i][j] for j in range(week * 6, (week + 1) * 6))


#On cree une variable pour indiquer les jours on l'on fait moins que le minimum
tooLowDay = LpVariable.dicts("tooLowDay", (range(n), range(nbWeek), range(m)), cat=LpBinary)
for i in range(n):
    for week in range(nbWeek):
        for j in range(m):
            if j == formationDayIndex:
                continue

            model += tooLowDay[i][week][j] >= (minHalfHourIfWorking - dayHalfHours[i][week][j]) / minHalfHourIfWorking - (1 - working[i][week][j])

#On cree une variable pour indiquer la différence entre le nombre d'heure travaillé et le max. Utilisé pour orienter notre recherche
# hoursDiff = LpVariable.dicts("hoursDiff", (range(n), range(m)), cat=LpBinary)
# for i in range(n):
#     for j in range(m):
#         model += hoursDiff[i][j] >= (maxHalfHour - dayHalfHours[i][j]) - (1 - working[i][j]) * maxHalfHour


#On cree une variable pour indiquer si un employee à un jour de repos dans la semaine
oneBreak = LpVariable.dicts("oneBreak", (range(n), range(nbWeek)), cat=LpBinary)
for i in range(n):
    for week in range(nbWeek):
        model += oneBreak[i][week] >= (lpSum(working[i][week][j] for j in range(m)) * (1/5)) - 1

if favoriseBreakNearSunday:
    #Variable qui symbolise la presence d'un congé le lundi ou le samedi
    sundayBreak = LpVariable.dicts("sundayBreak", (range(n), range(nbWeek)), cat=LpBinary)
    for i in range(n):
        for week in range(nbWeek):
            model += sundayBreak[i][week] >= working[i][week][0] + working[i][week][5] - 1

# if forceSundayBreak:
#     for i, shouldHaveSunday in enumerate(shoudlForceSunday):
#         if shouldHaveSunday:
#             for week in range(nbWeek):
#                 model += working[i][week][0] + working[i][week][5] - 1 <= 0

#On empêche de travailler les gens en formation le mercredi
for i in range(n):
    if inFormation[i]:
        #Pour chaque semaine, on ajoute la contrainte sur le Mecredi
        for week in range(nbWeek):
            model += lpSum(x[i][week][formationDayIndex][k] for k in range(0, formationStopHourIndex)) == 0

#Here we force employee to start only 1 time (no gape between work hours)
start = LpVariable.dicts("start", (range(n), range(nbWeek), range(m), range(o)), cat=LpBinary)
for i in range(n):
    for week in range(nbWeek):
        for j in range(m):

            #Force start to be equal to 1 if precedent hour is 0 and current is 1
            for k in range(o):
                if (k == 0):
                    model += start[i][week][j][k] == x[i][week][j][k]
                else:
                    #k - 1 doit valoir 0 et k doit valoir 1 pour que start soit contraint de valoir 1
                    model += start[i][week][j][k] >= (1 - x[i][week][j][k-1]) + x[i][week][j][k] - 1
            
            #Constraint the sum of start for 1 day and 1 employee to be less or equal to 1 (or 0 if it's a not working day)
            model += lpSum(start[i][week][j][k] for k in range(o)) <= working[i][week][j]

#Variable qui indique si un employee fait le break de midi le jour de formation
doTheBreak = LpVariable.dicts("doTheBreak", (range(n), range(nbWeek)), cat=LpBinary)
for i in range(n):
    for week in range(nbWeek):
        model += doTheBreak[i][week] == lpSum(start[i][week][formationDayIndex][k] for k in range(rushEndIndex, o))


#Variables qui indique si un employee commence le matin ou l'apres-midi
startEarly = LpVariable.dicts("startEarly", (range(n), range(nbWeek), range(m)), cat=LpBinary)
startLate = LpVariable.dicts("startLate", (range(n), range(nbWeek), range(m)), cat=LpBinary)
for i in range(n):
    for week in range(nbWeek):
        for j in range(m):
            model += startEarly[i][week][j] == lpSum(start[i][week][j][k] for k in range(0, earlyEnd))
            model += startLate[i][week][j] == lpSum(start[i][week][j][k] for k in range(rushEndIndex - 1, o))

# if forceEmployeeNbStart:
#     for i, nbStart in enumerate(nbStartRequired):
#         if nbStart == 0:
#             continue

#         model += lpSum(startEarly[i][week][j] for j in range(m)) >= nbStart

#Forcer les employee qui ont une pause en semaine à ne pas commencer le matin
for i in range(n):
    for week in range(nbWeek):
        for j in range(2, m):
            #Peut être verifier si il travaillais pas non plus j et j-2
            model += startLate[i][week][j-2] + startEarly[i][week][j] >= (1 - working[i][week][j-1])

#Chaque employee doit faire extactement son nombre d'heures (on rajoute le nombre de pause)
#TODO: remettre ==
diffWithContract = LpVariable.dicts("diffWithContract", (range(n), range(nbWeek)), lowBound=0, upBound=10, cat=LpContinuous)
for i in range(n):
    for week in range(nbWeek):
        sumOfAllHoursInWeek = lpSum(x[i][week][j][k] for j in range(m) for k in range(o))
        neededPauseInWeek = lpSum(needPause[i][week][j] for j in range(m))

        removeOnePause = 0

        #Si ils suivent la formation et qu'ils ne font pas le break, on ajoute 1 demi heure au temps de la semaine
        if inFormation[i]:
            removeOnePause = doTheBreak[i][week]

        model += diffWithContract[i][week] >= (pplWeekHours[i] * 2 + neededPauseInWeek) - sumOfAllHoursInWeek
        model += diffWithContract[i][week] >= sumOfAllHoursInWeek - (pplWeekHours[i] * 2 + neededPauseInWeek)

        # model += diffWithContract[i][week] >= (pplWeekHours[i] * 2 + workingDayInWeek[i][week]) - sumOfAllHoursInWeek
        # model += diffWithContract[i][week] >= sumOfAllHoursInWeek - (pplWeekHours[i] * 2 + workingDayInWeek[i][week])

        # model += sumOfAllHoursInWeek == (pplWeekHours[i] * 2 + neededPauseInWeek)

#Chaque employee ne peut faire que maxHalfHour demi-heures par jour
for i in range(n):
    for week in range(nbWeek):
        for j in range(m):

            if j == formationDayIndex and inFormation[i]:
                # maxHalfHourIcanDo =  # -1 car 30 min de pause pendant la formation et on garde nos 30min si pas de coupure
                
                model += lpSum(x[i][week][j][k] for k in range(o)) <= (maxHalfHoursPerDay[i] - formationStopHourIndex + 1 - doTheBreak[i][week])

            else:
                model += lpSum(x[i][week][j][k] for k in range(o)) <= maxHalfHoursPerDay[i]


### Regle de rush

#Il faut au moins une des personnes de atLeastOneIndex pendant le rush (sauf le jour de formation)
atLeastOne = LpVariable.dicts("atLeastOne", (range(nbWeek), range(m), range(rushStartIndex, rushEndIndex)), cat=LpBinary)
if atLeastOneIndex:
    for week in range(nbWeek):
        for j in range(m):

            if j == formationDayIndex:
                continue

            for k in range(rushStartIndex, rushEndIndex):
                if forceAtLeastOne:
                    model += lpSum(x[i][week][j][k] for i in atLeastOneIndex) >= 1
                else:
                    model += atLeastOne[week][j][k] >= 1 - lpSum(x[i][week][j][k] for i in atLeastOneIndex)

#Impossible de commencer pendant le rush
for i in range(n):
    for week in range(nbWeek):
        for j in range(m):

            reduceIndex = 0
            #TODO: voir si on garde le - 1
            # if j == formationDayIndex:
            #     reduceIndex = 1

            model += lpSum(start[i][week][j][k] for k in range(rushStartIndex, rushEndIndex - reduceIndex)) == 0

#This magical variable help the program to converge
presentDuringRush = LpVariable.dicts("presentDuringRush", (range(n), range(nbWeek), range(m), range(rushStartIndex, rushEndIndex)), cat=LpBinary)
for i in range(n):
    for week in range(nbWeek):
        for j in range(m):
            for k in range(rushStartIndex, rushEndIndex):
                model += presentDuringRush[i][week][j][k] >= (rushNbOpti - x[i][week][j][k]) / rushNbOpti

missingRush = LpVariable.dicts("missingRush", (range(nbWeek), range(m), range(rushStartIndex, rushEndIndex)), cat=LpBinary)
for week in range(nbWeek):
    for j in range(m):
    
        reduceIndex = 0
        # if j == formationDayIndex:
        #     reduceIndex = 1

        for k in range(rushStartIndex, rushEndIndex - reduceIndex):
            model += missingRush[week][j][k] >= (rushNbOpti - lpSum(x[i][week][j][k] for i in range(n))) / rushNbOpti


if reduceFormationDay:
    missingFormation = LpVariable.dicts("missingFormation", (range(nbWeek), range(m), range(formationReduceStart, formationReduceEnd)), cat=LpBinary)
    for week in range(nbWeek):
        for j in range(m):
            if j == formationDayIndex:
                for k in range(formationReduceStart, formationReduceEnd):
                    model += missingFormation[week][j][k] >= ((minimumPplCreFormation[k] + 1) - lpSum(x[i][week][j][k] for i in range(n))) / (minimumPplCreFormation[k] + 1)


if allowLateStart:
    for i, whatHourIndex in enumerate(startHour):
        if whatHourIndex != 0:
            model += lpSum(x[i][week][j][k] for week in range(nbWeek) for j in range(m) for k in range(whatHourIndex)) == 0



if activateNegativePair:
    negativePairPresent = LpVariable.dicts("negativePairPresent", (range(len(negativePairs)), range(nbWeek), range(m), range(o)), cat=LpBinary)
    for pairIndex, pair in enumerate(negativePairs):
        i1 = pair[0]
        i2 = pair[1]
        for week in range(nbWeek):
            for j in range(m):
                for k in range(o):
                    model += negativePairPresent[pairIndex][week][j][k] >= x[i1][week][j][k] + x[i2][week][j][k] - 1


started = LpVariable.dicts("started", (range(n), range(nbWeek)), cat=LpBinary)
finished = LpVariable.dicts("finished", (range(n), range(nbWeek)), cat=LpBinary)
for i in range(n):
    for week in range(nbWeek):
        model += started[i][week] * m >= lpSum(startEarly[i][week][j] for j in range(m) if j != formationDayIndex)
        model += finished[i][week] * m >= lpSum(startLate[i][week][j] for j in range(m) if j != formationDayIndex)
        
#Contrainte pour forcer un employee a ne faire que le matin ou que l'après midi pendant toute la semaine (sauf le jour de formation)
if forceSameStartDuringWeek:
    for i in range(n):
        for week in range(nbWeek):
            model += started[i][week] + finished[i][week] <= 1

# if forceEarly:
#     for i, isEarly in enumerate(needStartEarly):
#         if isEarly:
#             model += started[i][0] == 1

# if forceLate:
#     for i, isLate in enumerate(needStartLate):
#         if isLate:
#             model += finished[i][0] == 1

#Contrainte pour forcer les personnes ont des imperatifs à ne pas être là
# if activateRestrictions:

#     #Pour ceux qui doivent finir avant tel heure
#     for i, pplEndRestrictions in enumerate(endBefore):
#         for endRestriction in pplEndRestrictions:
#             j = endRestriction[0]
#             startingRestriction = endRestriction[1]
#             #On force x[i][j][k] à valoir 0 de startingRestriction à la fin
#             model += lpSum(x[i][j][k] for k in range(startingRestriction, o)) == 0

#     #Pour ceux qui sont absent pendant une range
#     for i, pplRangeRestrictions in enumerate(absentRange):
#         for rangeRestriction in pplRangeRestrictions:
#             j = rangeRestriction[0]
#             startingRestriction = rangeRestriction[1]
#             endingRestriction = rangeRestriction[2]
#             #On force x[i][j][k] à valoir 0 de startingRestriction à endingRestriction
#             model += lpSum(x[i][j][k] for k in range(startingRestriction, endingRestriction)) == 0


#Objective
# model += lpSum(x[i][j][k] for i in range(n) for j in range(m) for k in range(o))
# model += lpSum(working[i][j] for i in range(n) for j in range(m)) / n
# model += 


objectiveFunc = LpAffineExpression()

objectiveFunc += lpSum(oneBreak[i][week] for i in range(n) for week in range(nbWeek)) * 100000000000 #Mendatory
objectiveFunc += lpSum(diffWithContract[i][week] for i in range(n) for week in range(nbWeek)) * 1000000000 #Mendatory

objectiveFunc += lpSum(tooLowDay[i][week][j] for i in range(n) for week in range(nbWeek) for j in range(m)) * 1000000 #Can be discussed
objectiveFunc += lpSum(missingRush[week][j][k] for week in range(nbWeek) for j in range(m) for k in range(rushStartIndex, rushEndIndex)) * 10000 #Can be discussed

if atLeastOneIndex and not forceAtLeastOne:
    objectiveFunc += lpSum(atLeastOne[week][j][k] for week in range(nbWeek) for j in range(m) for k in range(rushStartIndex, rushEndIndex)) * 10000000

if allowOneMoreHalfHour:
    objectiveFunc += lpSum(sixHoursDay[i][week][j] for i in range(n) for week in range(nbWeek) for j in range(m)) * 1000000

if reduceFormationDay:
    objectiveFunc += lpSum(missingFormation[week][j][k] for week in range(nbWeek) for j in range(m) for k in range(formationReduceStart, formationReduceEnd)) * 1

if favoriseBreakNearSunday:
    objectiveFunc += lpSum(sundayBreak[i][week] for i in range(n) for week in range(nbWeek)) * 10


if activateNegativePair:
    objectiveFunc += lpSum(negativePairPresent[pairIndex][week][j][k] for pairIndex in range(len(negativePairs)) for week in range(nbWeek) for j in range(m) for k in range(o)) * 100

if repartir:
    objectiveFunc += maxEmployee * (1/10)

model += objectiveFunc


    #    + lpSum(respectedCharge[j][k] for j in range(m) for k in range(o)) * 10000000 \

    #    + lpSum(presentDuringRush[i][j][k] for i in range(n) for j in range(m) for k in range(rushStartIndex, rushEndIndex)) \



       
 #Pour essayer de ne manquer de personne pendant le rush
 #Pour essayer de ne manquer de personne pendant le rush
# + lpSum(hoursDiff[i][j] for i in range(n) for j in range(m)) \

# print(model)


# Solve the problem
status = model.solve(PULP_CBC_CMD(maxSeconds=maxExecutionTime))

print(f"status: {model.status}, {LpStatus[model.status]}")

#print(f"objective: {model.objective.value()}")
for var in model.variables():
    print(f"{var.name}: {var.value()}")

print(f"status: {model.status}, {LpStatus[model.status]}")
print(f"objective: {model.objective.value()}")

if model.status != 1:
    exit(0)


employeeHours = []

for i in range(n):

    # for week in range(nbWeek):
    #     print(f"{pplName[i]}: weekNb={week}, nbPause: {oneBreak[i][week].value()}")
    #     print(f"{pplName[i]}: Diff with contract: {diffWithContract[i][week].value()}")
    #     print(f"Have sundayBreak: {sundayBreak[i][week].value()}")

    #     for j in range(m):
    #         print(f"{j}: {startEarly[i][week][j].value()}, working: {working[i][j].value()}")

    #     sumOfAllHoursInWeek = 0
    #     neededPauseInWeek = 0
    #     for j in range(week * 6, (week + 1) * 6):
    #         for k in range(o):
    #             sumOfAllHoursInWeek += x[i][j][k].value()

    #         neededPauseInWeek += needPause[i][j].value()

    #     print(f"{diffWithContract[i][week].value()} >= ({pplWeekHours[i] * 2} + {neededPauseInWeek}) - {sumOfAllHoursInWeek}")
    #     print(f"{diffWithContract[i][week].value()} >= {sumOfAllHoursInWeek} - ({pplWeekHours[i] * 2} + {neededPauseInWeek})")


    #     # for j in range(week * 6, (week + 1) * 6):
    #     #     print(f"{j}: sixHoursDay = {sixHoursDay[i][j].value()}", f"DayHalfHour = {dayHalfHours[i][j].value()}")

    #     # print(f"WorkingDay in week: {workingDayInWeek[i][week].value()}")

    employeeHours.append([])
    for j in range(m):
        start = 0
        end = 0
        for k in range(o):
            hour = k*0.5 + 8.5
            if x[i][j][k].value() != 0:
                if start == 0:
                    start = hour
                if end != 0:
                    print("ERROR")
            else:
                if start != 0 and end == 0:
                    end = hour

        if start != 0 and end == 0:
            end = k*0.5 + 8.5 + 0.5

        if start == 0 and end == 0:
            employeeHours[-1].append([])
        else:
            employeeHours[-1].append([start, end])
                
        print(f"{pplName[i]}: {start} -> {end} ({dayHalfHours[i][j].value() / 2} --> {tooLowDay[i][j].value()})")

print("HERE:")
print(f"objective: {model.objective.value()}")


print("Objective results:")

print("one break: ",  sum(oneBreak[i][week].value() for i in range(n) for week in range(nbWeek)))

print("diff With Contract: ", sum(diffWithContract[i][week].value() for i in range(n) for week in range(nbWeek)))

print("missing Rush: ", sum(missingRush[week][j][k].value() for week in range(nbWeek) for j in range(m) for k in range(rushStartIndex, rushEndIndex)))
print("too Low Day: ", sum(tooLowDay[i][week][j].value() for i in range(n) for week in range(nbWeek) for j in range(m)))

if atLeastOneIndex and not forceAtLeastOne:
    print("at least one: ", sum(atLeastOne[week][j][k].value() for week in range(nbWeek) for j in range(m) for k in range(rushStartIndex, rushEndIndex)))

if allowOneMoreHalfHour:
    print("six Hours Day: ", sum(sixHoursDay[i][week][j].value() for i in range(n) for week in range(nbWeek) for j in range(m)))

if reduceFormationDay:
    print("missing Formation: ", sum(missingFormation[week][j][k].value() for week in range(nbWeek) for j in range(m) for k in range(formationReduceStart, formationReduceEnd)))

if favoriseBreakNearSunday:
    print("sunday Break: ", sum(sundayBreak[i][week].value() for i in range(n) for week in range(nbWeek)))


if activateNegativePair:
    print("negative Pair Present: ", sum(negativePairPresent[pairIndex][week][j][k].value() for pairIndex in range(len(negativePairs)) for week in range(nbWeek) for j in range(m) for k in range(o)))

if repartir:
    print("Max employee: ", maxEmployee.value())


# for i in range(n):
# for j in range(m):
#     print(f"{j} : ", end="")
#     for k in range(rushStartIndex, rushEndIndex):
#         print(f"{k}={missingRush[j][k].value()}", end=" ")
    
#     print(" ")

print(employeeHours)
visualize(employeeHours, pplName)