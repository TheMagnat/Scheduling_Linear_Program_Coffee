
from pulp import LpMinimize, LpMaximize, LpProblem, LpStatus, lpSum, LpVariable, LpBinary, LpInteger, LpContinuous, LpConstraint, LpAffineExpression, PULP_CBC_CMD
import numpy as np

#Global parameters
maxExecutionTime = 120
allowOneMoreHalfHour = True
favoriseBreakNearSunday = True
repartir = True
rushNbOpti = 3

earlyEnd = 7

#Rush
rushStartIndex = 7
rushEndIndex = 12

#Formation
formationDayIndex = 2
formationStopHourIndex = 6 #Ils arrêtent la formation à 11h30

#Favoriser une solution avec des gens en plus a la fin d'une journée de formation
reduceFormationDay = True
formationReduceStart = 16
formationReduceEnd = 21

nbHalfHourToPause = 4 * 2 #4h de travail = une pause

#+1 pour la pause de 30min
# maxHalfHour = 5*2 + 1 #5 hours
minHalfHourIfWorking = 2*2 + 1 #5 hours

#RENDRE PARAMETRABLE
forceSameStartDuringWeek = True
activateRestrictions = True

#Equipier dont il faut au moins 1 le midi
forceAtLeastOne = False
atLeastOneIndex = [0, 1]

#Pour insiter l'algorithme à eviter de mettre ces paires ensemble
activateNegativePair = True
negativePairs = [[2, 4], [3, 6], [0, 1]]


class WeekData:
    def __init__(self, minimumPplCre, minimumPplCreMonday, minimumPplCreFormation):
        self.minimumPplCre = minimumPplCre
        self.minimumPplCreMonday = minimumPplCreMonday
        self.minimumPplCreFormation = minimumPplCreFormation


class WeekLP:

    def __init__(self):
        # Create the model
        self.model = LpProblem(name="Café", sense=LpMinimize)


    def generate(self, weekData, pplWeekHours, maxHalfHoursPerDay, inFormation, startHour, endBefore, absentRange, shouldForceSunday, needStartEarly, needStartLate):
        
        n = len(pplWeekHours) #Nb d'employées
        m = 6 #Nb de jours
        o = len(weekData.minimumPplCre) #Nb de demi-heures

        self.n = n
        self.m = m
        self.o = o

        # Create a dictionary to store the variables
        self.x = LpVariable.dicts("x", (range(n), range(m), range(o)), cat=LpBinary)


        #Chaque demi heure doit avoir au moins le nombre d'employee minimum de minimumPplCre
        if repartir:
            self.maxEmployee = LpVariable("maxEmployee", lowBound=0, upBound=n, cat=LpContinuous)

        self.respectedCharge = LpVariable.dicts("respectedCharge", (range(m), range(o)), lowBound=0, upBound=3, cat=LpContinuous)
        for j in range(m):
            for k in range(o):
                weekDay = j%6

                currentConstantList = []

                if weekDay == 0:
                    currentConstant = weekData.minimumPplCreMonday[k]
                elif weekDay == formationDayIndex:
                    currentConstant = weekData.minimumPplCreFormation[k]
                else:
                    currentConstant = weekData.minimumPplCre[k]


                if currentConstant == 0:
                    self.model += lpSum(self.x[i][j][k] for i in range(n)) == 0
                else:
                    self.model += lpSum(self.x[i][j][k] for i in range(n)) >= currentConstant

                    if repartir:
                        self.model += self.maxEmployee >= lpSum(self.x[i][j][k] for i in range(n)) - currentConstant
                    # self.model += self.respectedCharge[j][k] >= currentConstant - lpSum(self.x[i][j][k] for i in range(n))


        #On cree une variable pour indiquer le nombre de demi-heures que travail un employee par jour
        self.dayHalfHours = LpVariable.dicts("dayHalfHours", (range(n), range(m)), lowBound=0, upBound=o, cat=LpInteger)
        for i in range(n):
            for j in range(m):
                self.model += self.dayHalfHours[i][j] == lpSum(self.x[i][j][k] for k in range(o))


        if allowOneMoreHalfHour:
            self.sixHoursDay = LpVariable.dicts("sixHoursDay", (range(n), range(m)), cat=LpBinary)
            for i in range(n):
                for j in range(m):
                    #print( maxHalfHoursPerDay[i], maxHalfHoursPerDay[i] - 1)
                    self.model += self.sixHoursDay[i][j] >= self.dayHalfHours[i][j] - (maxHalfHoursPerDay[i] - 1)


        #On cree une variable pour indiquer si un employee prendra une pause ce jour
        self.needPause = LpVariable.dicts("needPause", (range(n), range(m)), cat=LpBinary)
        self.z = LpVariable.dicts("z", (range(n), range(m)), cat=LpBinary)
        for i in range(n):
            for j in range(m):
                self.model += self.z[i][j] * nbHalfHourToPause >= nbHalfHourToPause - self.dayHalfHours[i][j]
                self.model += self.needPause[i][j] <= 1 - self.z[i][j]
                self.model += self.needPause[i][j] * o >= self.dayHalfHours[i][j] - (nbHalfHourToPause - 1)

                # self.model += self.needPause[i][j] * o >= self.dayHalfHours[i][j] - (nbHalfHourToPause - 1)
                # self.model += self.needPause[i][j] * nbHalfHourToPause <= self.dayHalfHours[i][j]


        #On cree une variable pour indiquer si un employee travail le jour j ou non
        #TODO: try with Z too
        self.working = LpVariable.dicts("working", (range(n), range(m)), cat=LpBinary)
        for i in range(n):
            for j in range(m):
                self.model += self.working[i][j] * maxHalfHoursPerDay[i] >= self.dayHalfHours[i][j] #For working to be equal to 1 if dayHalfHours is equal to more than 1
                self.model += self.working[i][j] <= self.dayHalfHours[i][j] #Force working to be equal to 0 if dayHalfHours is equal to 0

        #Variable représentant le nombre de jour travaille pour chaque equipier dans une semaine
        # workingDayInWeek = LpVariable.dicts("workingDayInWeek", (range(n), range(nbWeek)), lowBound=0, upBound=6, cat=LpInteger)
        # for i in range(n):
        #     for week in range(nbWeek):
        #         self.model += workingDayInWeek[i][week] == lpSum(self.working[i][j] for j in range(week * 6, (week + 1) * 6))


        #On cree une variable pour indiquer les jours on l'on fait moins que le minimum
        self.tooLowDay = LpVariable.dicts("tooLowDay", (range(n), range(m)), cat=LpBinary)
        for i in range(n):
            for j in range(m):
                if j == formationDayIndex:
                    continue

                self.model += self.tooLowDay[i][j] >= (minHalfHourIfWorking - self.dayHalfHours[i][j]) / minHalfHourIfWorking - (1 - self.working[i][j])

        #On cree une variable pour indiquer la différence entre le nombre d'heure travaillé et le max. Utilisé pour orienter notre recherche
        # hoursDiff = LpVariable.dicts("hoursDiff", (range(n), range(m)), cat=LpBinary)
        # for i in range(n):
        #     for j in range(m):
        #         self.model += hoursDiff[i][j] >= (maxHalfHour - self.dayHalfHours[i][j]) - (1 - self.working[i][j]) * maxHalfHour


        #On cree une variable pour indiquer si un employee à un jour de repos dans la semaine
        self.oneBreak = LpVariable.dicts("oneBreak", (range(n)), cat=LpBinary)
        for i in range(n):
            self.model += self.oneBreak[i] >= (lpSum(self.working[i][j] for j in range(m)) * (1/5)) - 1

        if favoriseBreakNearSunday:
            #Variable qui symbolise la presence d'un congé le lundi ou le samedi
            self.sundayBreak = LpVariable.dicts("sundayBreak", (range(n)), cat=LpBinary)
            for i in range(n):
                self.model += self.sundayBreak[i] >= self.working[i][0] + self.working[i][5] - 1

        for i, shouldHaveSunday in enumerate(shouldForceSunday):
            if shouldHaveSunday:
                self.model += self.working[i][0] + self.working[i][5] - 1 <= 0

        #On empêche de travailler les gens en formation le mercredi
        for i in range(n):
            if inFormation[i]:
                self.model += lpSum(self.x[i][formationDayIndex][k] for k in range(0, formationStopHourIndex)) == 0

        #Here we force employee to self.start only 1 time (no gape between work hours)
        self.start = LpVariable.dicts("start", (range(n), range(m), range(o)), cat=LpBinary)
        for i in range(n):
            for j in range(m):

                #Force start to be equal to 1 if precedent hour is 0 and current is 1
                for k in range(o):
                    if (k == 0):
                        self.model += self.start[i][j][k] == self.x[i][j][k]
                    else:
                        #k - 1 doit valoir 0 et k doit valoir 1 pour que self.start soit contraint de valoir 1
                        self.model += self.start[i][j][k] >= (1 - self.x[i][j][k-1]) + self.x[i][j][k] - 1
                
                #Constraint the sum of start for 1 day and 1 employee to be less or equal to 1 (or 0 if it's a not self.working day)
                self.model += lpSum(self.start[i][j][k] for k in range(o)) <= self.working[i][j]

        #Variable qui indique si un employee fait le break de midi le jour de formation
        self.doTheBreak = LpVariable.dicts("doTheBreak", (range(n)), cat=LpBinary)
        j = formationDayIndex
        for i in range(n):
            self.model += self.doTheBreak[i] == lpSum(self.start[i][j][k] for k in range(rushEndIndex, o))


        #Variables qui indique si un employee commence le matin ou l'apres-midi
        self.startEarly = LpVariable.dicts("startEarly", (range(n), range(m)), cat=LpBinary)
        self.startLate = LpVariable.dicts("startLate", (range(n), range(m)), cat=LpBinary)
        for i in range(n):
            for j in range(m):
                self.model += self.startEarly[i][j] == lpSum(self.start[i][j][k] for k in range(0, earlyEnd))
                self.model += self.startLate[i][j] == lpSum(self.start[i][j][k] for k in range(rushEndIndex - 1, o))

        # if forceEmployeeNbStart:
        #     for i, nbStart in enumerate(nbStartRequired):
        #         if nbStart == 0:
        #             continue

        #         self.model += lpSum(self.startEarly[i][j] for j in range(m)) >= nbStart

        #Forcer les employee qui ont une pause en semaine à ne pas commencer le matin
        for i in range(n):
            for j in range(2, m):
                #Peut être verifier si il travaillais pas non plus j et j-2
                self.model += self.startLate[i][j-2] + self.startEarly[i][j] >= (1 - self.working[i][j-1])

        #Chaque employee doit faire extactement son nombre d'heures (on rajoute le nombre de pause = au nombre de jours travaillé)
        #TODO: remettre ==
        self.diffWithContract = LpVariable.dicts("diffWithContract", (range(n)), lowBound=0, upBound=10, cat=LpContinuous)
        for i in range(n):
            sumOfAllHoursInWeek = lpSum(self.x[i][j][k] for j in range(m) for k in range(o))
            neededPauseInWeek = lpSum(self.needPause[i][j] for j in range(m))

            removeOnePause = 0

            #Si ils suivent la formation et qu'ils ne font pas le break, on ajoute 1 demi heure au temps de la semaine
            if inFormation[i]:
                removeOnePause = self.doTheBreak[i]

            self.model += self.diffWithContract[i] >= (pplWeekHours[i] * 2 + neededPauseInWeek) - sumOfAllHoursInWeek
            self.model += self.diffWithContract[i] >= sumOfAllHoursInWeek - (pplWeekHours[i] * 2 + neededPauseInWeek)

            # self.model += self.diffWithContract[i][week] >= (pplWeekHours[i] * 2 + workingDayInWeek[i][week]) - sumOfAllHoursInWeek
            # self.model += self.diffWithContract[i][week] >= sumOfAllHoursInWeek - (pplWeekHours[i] * 2 + workingDayInWeek[i][week])

            # self.model += sumOfAllHoursInWeek == (pplWeekHours[i] * 2 + neededPauseInWeek)

        #Chaque employee ne peut faire que maxHalfHour demi-heures par jour
        for i in range(n):
            for j in range(m):

                if j == formationDayIndex and inFormation[i]:
                    # maxHalfHourIcanDo =  # -1 car 30 min de pause pendant la formation et on garde nos 30min si pas de coupure
                    
                    self.model += lpSum(self.x[i][j][k] for k in range(o)) <= (maxHalfHoursPerDay[i] - formationStopHourIndex + 1 - self.doTheBreak[i])

                else:
                    self.model += lpSum(self.x[i][j][k] for k in range(o)) <= maxHalfHoursPerDay[i]


        ### Regle de rush

        #Il faut au moins une des personnes de atLeastOneIndex pendant le rush (sauf le jour de formation)
        self.atLeastOne = LpVariable.dicts("atLeastOne", (range(m), range(rushStartIndex, rushEndIndex)), cat=LpBinary)
        if atLeastOneIndex:
            for j in range(m):

                if j == formationDayIndex:
                    continue

                for k in range(rushStartIndex, rushEndIndex):
                    if forceAtLeastOne:
                        self.model += lpSum(self.x[i][j][k] for i in atLeastOneIndex) >= 1
                    else:
                        self.model += self.atLeastOne[j][k] >= 1 - lpSum(self.x[i][j][k] for i in atLeastOneIndex)

        #Impossible de commencer pendant le rush
        for i in range(n):
            for j in range(m):

                reduceIndex = 0
                #TODO: voir si on garde le - 1
                # if j == formationDayIndex:
                #     reduceIndex = 1

                self.model += lpSum(self.start[i][j][k] for k in range(rushStartIndex, rushEndIndex - reduceIndex)) == 0

        #This magical variable help the program to converge
        self.presentDuringRush = LpVariable.dicts("presentDuringRush", (range(n), range(m), range(rushStartIndex, rushEndIndex)), cat=LpBinary)
        for i in range(n):
            for j in range(m):
                for k in range(rushStartIndex, rushEndIndex):
                    self.model += self.presentDuringRush[i][j][k] >= (rushNbOpti - self.x[i][j][k]) / rushNbOpti

        self.missingRush = LpVariable.dicts("missingRush", (range(m), range(rushStartIndex, rushEndIndex)), cat=LpBinary)
        for j in range(m):
            
            reduceIndex = 0
            # if j == formationDayIndex:
            #     reduceIndex = 1

            for k in range(rushStartIndex, rushEndIndex - reduceIndex):
                self.model += self.missingRush[j][k] >= (rushNbOpti - lpSum(self.x[i][j][k] for i in range(n))) / rushNbOpti


        if reduceFormationDay:
            self.missingFormation = LpVariable.dicts("missingFormation", (range(m), range(formationReduceStart, formationReduceEnd)), cat=LpBinary)
            for j in range(m):
                for k in range(formationReduceStart, formationReduceEnd):
                    self.model += self.missingFormation[j][k] >= ((weekData.minimumPplCreFormation[k] + 1) - lpSum(self.x[i][j][k] for i in range(n))) / (weekData.minimumPplCreFormation[k] + 1)


        # if allowLateStart:
        for i, whatHourIndex in enumerate(startHour):
            if whatHourIndex != 0:
                self.model += lpSum(self.x[i][j][k] for j in range(m) for k in range(whatHourIndex)) == 0



        if activateNegativePair:
            self.negativePairPresent = LpVariable.dicts("negativePairPresent", (range(len(negativePairs)), range(m), range(o)), cat=LpBinary)
            for pairIndex, pair in enumerate(negativePairs):
                i1 = pair[0]
                i2 = pair[1]
                for j in range(m):
                    for k in range(o):
                        self.model += self.negativePairPresent[pairIndex][j][k] >= self.x[i1][j][k] + self.x[i2][j][k] - 1


        self.started = LpVariable.dicts("self.started", (range(n)), cat=LpBinary)
        self.finished = LpVariable.dicts("self.finished", (range(n)), cat=LpBinary)
        for i in range(n):
            self.model += self.started[i] * m >= lpSum(self.startEarly[i][j] for j in range(m) if j != formationDayIndex)
            self.model += self.finished[i] * m >= lpSum(self.startLate[i][j] for j in range(m) if j != formationDayIndex)

        #Contrainte pour forcer un employee a ne faire que le matin ou que l'après midi pendant toute la semaine (sauf le jour de formation)
        if forceSameStartDuringWeek:
            for i in range(n):
                self.model += self.started[i] + self.finished[i] - 1 <= 0

        # if forceEarly:
        for i, isEarly in enumerate(needStartEarly):
            if isEarly:
                self.model += self.started[i] == 1

        # if forceLate:
        for i, isLate in enumerate(needStartLate):
            if isLate:
                self.model += self.finished[i] == 1

        #Contrainte pour forcer les personnes ont des imperatifs à ne pas être là
        if activateRestrictions:

            #Pour ceux qui doivent finir avant tel heure
            for i, pplEndRestrictions in enumerate(endBefore):
                for endRestriction in pplEndRestrictions:
                    j = endRestriction[0]
                    startingRestriction = endRestriction[1]
                    #On force self.x[i][j][k] à valoir 0 de startingRestriction à la fin
                    self.model += lpSum(self.x[i][j][k] for k in range(startingRestriction, o)) == 0

            #Pour ceux qui sont absent pendant une range
            for i, pplRangeRestrictions in enumerate(absentRange):
                for rangeRestriction in pplRangeRestrictions:
                    j = rangeRestriction[0]
                    startingRestriction = rangeRestriction[1]
                    endingRestriction = rangeRestriction[2]
                    #On force self.x[i][j][k] à valoir 0 de startingRestriction à endingRestriction
                    self.model += lpSum(self.x[i][j][k] for k in range(startingRestriction, endingRestriction)) == 0

                
        objectiveFunc = LpAffineExpression()

        objectiveFunc += lpSum(self.oneBreak[i] for i in range(n)) * 100000000000 #Mendatory
        objectiveFunc += lpSum(self.diffWithContract[i] for i in range(n)) * 1000000000 #Mendatory

        objectiveFunc += lpSum(self.tooLowDay[i][j] for i in range(n) for j in range(m)) * 1000000 #Can be discussed
        objectiveFunc += lpSum(self.missingRush[j][k] for j in range(m) for k in range(rushStartIndex, rushEndIndex)) * 10000 #Can be discussed

        if atLeastOneIndex and not forceAtLeastOne:
            objectiveFunc += lpSum(self.atLeastOne[j][k] for j in range(m) for k in range(rushStartIndex, rushEndIndex)) * 10000000

        if allowOneMoreHalfHour:
            objectiveFunc += lpSum(self.sixHoursDay[i][j] for i in range(n) for j in range(m)) * 1000000

        if reduceFormationDay:
            objectiveFunc += lpSum(self.missingFormation[j][k] for j in range(m) for k in range(formationReduceStart, formationReduceEnd)) * 1

        if favoriseBreakNearSunday:
            objectiveFunc += lpSum(self.sundayBreak[i] for i in range(n)) * 10


        if activateNegativePair:
            objectiveFunc += lpSum(self.negativePairPresent[pairIndex][j][k] for pairIndex in range(len(negativePairs)) for j in range(m) for k in range(o)) * 100

        if repartir:
            objectiveFunc += self.maxEmployee * (1/10)

        self.model += objectiveFunc


    def solve(self):
        # Solve the problem
        status = self.model.solve(PULP_CBC_CMD(maxSeconds=maxExecutionTime))

        #If the objective value is greater than 1000000000, it means that the solution violate a mendatory constraint
        if status == 1 and self.model.objective.value() >= 1000000000:
            status = 0

        return status, self.model.objective.value()

    def printObjectives(self):
        print("Objective results:")

        print("one break: ",  sum(self.oneBreak[i].value() for i in range(self.n)))

        print("diff With Contract: ", sum(self.diffWithContract[i].value() for i in range(self.n)))

        print("missing Rush: ", sum(self.missingRush[j][k].value() for j in range(self.m) for k in range(rushStartIndex, rushEndIndex)))
        print("too Low Day: ", sum(self.tooLowDay[i][j].value() for i in range(self.n) for j in range(self.m)))

        if atLeastOneIndex and not forceAtLeastOne:
            print("at least one: ", sum(self.atLeastOne[j][k].value() for j in range(self.m) for k in range(rushStartIndex, rushEndIndex)))

        if allowOneMoreHalfHour:
            print("six Hours Day: ", sum(self.sixHoursDay[i][j].value() for i in range(self.n) for j in range(self.m)))

        if reduceFormationDay:
            print("missing Formation: ", sum(self.missingFormation[j][k].value() for j in range(self.m) for k in range(formationReduceStart, formationReduceEnd)))

        if favoriseBreakNearSunday:
            print("sunday Break: ", sum(self.sundayBreak[i].value() for i in range(self.n)))


        if activateNegativePair:
            print("negative Pair Present: ", sum(self.negativePairPresent[pairIndex][j][k].value() for pairIndex in range(len(negativePairs)) for j in range(self.m) for k in range(self.o)))

        if repartir:
            print("Max employee: ", self.maxEmployee.value())

        print("Total score:", self.model.objective.value())

    #Return 1 if got the Sunday break, 0 if not
    def getSundays(self):
        sundays = np.empty(self.n, dtype=int)
        for i in range(self.n):
            sundays[i] = 1 - self.sundayBreak[i].value()
                
        return sundays

    #Return 0 if i started, 1 if i finished
    def getStarting(self):
        starting = np.empty(self.n, dtype=int)
        for i in range(self.n):
            if self.started[i].value() == 1:
                starting[i] = 0
            elif self.finished[i].value() == 1:
                starting[i] = 1
            else:
                print("ERROR")
                
        return starting

    def getScheduling(self):
        employeeHours = []
        for i in range(self.n):
            employeeHours.append([])
            for j in range(self.m):
                self.start = 0
                end = 0
                for k in range(self.o):
                    hour = k*0.5 + 8.5
                    if self.x[i][j][k].value() != 0:
                        if self.start == 0:
                            self.start = hour
                        if end != 0:
                            print("ERROR")
                    else:
                        if self.start != 0 and end == 0:
                            end = hour

                if self.start != 0 and end == 0:
                    end = k*0.5 + 8.5 + 0.5

                if self.start == 0 and end == 0:
                    employeeHours[-1].append([])
                else:
                    employeeHours[-1].append([self.start, end])
                        
                # print(f"{pplName[i]}: {self.start} -> {end} ({self.dayHalfHours[i][j].value() / 2} --> {self.tooLowDay[i][j].value()})")

        return employeeHours