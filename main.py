
from pulp import LpMinimize, LpMaximize, LpProblem, LpStatus, lpSum, LpVariable, LpBinary, LpInteger, LpConstraint, PULP_CBC_CMD

from visu import visualize

### Param
maxExecutionTime = 10

#Data of the problem
nbWeek = 1 #Nb semaines
m = nbWeek * 6 #Nb jours

#+1 pour la pause de 30min
maxHalfHour = 5*2 + 1 #5 hours
minHalfHourIfWorking = 1 + 2*2 #5 hours

#Nombre d'employee minimum par demi heure
#  0    1    2     3     4     5     6     7     8     9     10   11    12     13    14   15    16
#[8h30, 9h, 9h30, 10h, 10h30, 11h, 11h30, 12h, 12h30, 13h, 13h30, 14h, 14h30, 15h, 15h30, 16h, 16h30, // 17h, 17h30, 18h, 18h30, 19h, 19h30],
minimumPplCre          = [1, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2]
minimumPplCreMonday    = [0, 0, 1, 2, 2, 2, 2, 3, 3, 3, 3, 3, 1, 1, 1, 1, 2, 2, 0, 0, 0, 0, 0]
minimumPplCreFormation = [1, 1, 1, 1, 1, 1, 2, 3, 3, 3, 3, 3, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2]
# 8h30 11h30
rushNbOpti = 3

rushStartIndex = 7
rushEndIndex = 12

#Houre que dois faire un employee par semaine
pplWeekHours = [20, 25, 20, 20, 24, 25, 20]
pplName = ["Chloé", "Maeva", "Johanne", "Alexis", "Thomas", "Line", "Philippine"]
inFormation = [True, False, True, True, True, True, True]
formationStopHourIndex = 6 #Ils arrêtent la formation à 11h30

#Equipier dont il faut au moins 1 le midi
atLeastOneIndex = [0, 1]

#Pour Line, à utiliser plus tard
mustStartLate = [False, False, False, False, False, True, False]
startHour = [0, 0, 0, 0, 0, 7, 0]

n = len(pplWeekHours) #Nb Employee
o = len(minimumPplCre) #Nb demi-heures

""" Questions
Cb de jours de repos minimum par semaine en + du dimanche ?
Cb d'heures minimum par jour si il vient ?
Le nb minimum en fonctions des horraires

OK - jusqua 16h30 on peut mettre 1
OK - Ne pas arriver au millieux de service (avant midi)

Chloé ou Maeva au moins là pour Midi

Lin pas les matins (12h mini)

On peut relacher le midi à 2 employées

Binome: Thomas Joanne
        Alexis Philipine
        Chloé et Maeva
        
ceux à 20h seulement 4h
exeptionnellement 6h
1 jour de congé par semaine,
favoriser de le coller au dimanche
"""


# Create the model
model = LpProblem(name="Café", sense=LpMinimize)

# Create a dictionary to store the variables
x = LpVariable.dicts("x", (range(n), range(m), range(o)), cat=LpBinary)


#Chaque demi heure doit avoir au moins le nombre d'employee minimum de minimumPplCre
for j in range(m):
    for k in range(o):
        weekDay = j%6
        print(weekDay)
        if weekDay == 0:
            model += lpSum(x[i][j][k] for i in range(n)) >= minimumPplCreMonday[k]
        elif weekDay == 2:
            model += lpSum(x[i][j][k] for i in range(n)) >= minimumPplCreFormation[k]
        else:
            model += lpSum(x[i][j][k] for i in range(n)) >= minimumPplCre[k]

#Chaque employee doit faire extactement son nombre d'heures
#TODO: remettre ==
for i in range(n):
    for week in range(nbWeek):
        model += lpSum(x[i][j][k] for j in range(week * 6, (week + 1) * 6) for k in range(o)) == pplWeekHours[i] * 2


#Chaque employee ne peut faire que maxHalfHour demi-heures par jour
for i in range(n):
    for j in range(m):
        model += lpSum(x[i][j][k] for k in range(o)) <= maxHalfHour

#On cree une variable pour indiquer le nombre de demi-heures que travail un employee par jour
dayHalfHours = LpVariable.dicts("dayHalfHours", (range(n), range(m)), cat=LpInteger)
for i in range(n):
    for j in range(m):
        model += dayHalfHours[i][j] == lpSum(x[i][j][k] for k in range(o))

#On cree une variable pour indiquer si un employee travail le jour j ou non
working = LpVariable.dicts("working", (range(n), range(m)), cat=LpBinary)
for i in range(n):
    for j in range(m):
        model += working[i][j] >= dayHalfHours[i][j] * (1/o)

#On cree une variable pour indiquer les jours on l'on fait moins que le minimum
tooLowDay = LpVariable.dicts("tooLowDay", (range(n), range(m)), cat=LpBinary)
for i in range(n):
    for j in range(m):
        model += tooLowDay[i][j] >= (minHalfHourIfWorking - dayHalfHours[i][j]) / minHalfHourIfWorking - (1 - working[i][j])

#On cree une variable pour indiquer la différence entre le nombre d'heure travaillé et le max. Utilisé pour orienter notre recherche
# hoursDiff = LpVariable.dicts("hoursDiff", (range(n), range(m)), cat=LpBinary)
# for i in range(n):
#     for j in range(m):
#         model += hoursDiff[i][j] >= (maxHalfHour - dayHalfHours[i][j]) - (1 - working[i][j]) * maxHalfHour


#On cree une variable pour indiquer si un employee à un jour de pause dans la semaine
onePause = LpVariable.dicts("onePause", (range(n), range(nbWeek)), cat=LpBinary)
for i in range(n):
    for week in range(nbWeek):
        model += onePause[i][week] >= (lpSum(working[i][j] for j in range(week * 6, (week + 1) * 6)) / 5) - 1

#On empêche de travailler les gens en formation le mercredi
j = 2
for i in range(n):
    if inFormation[i]:
        #Pour chaque semaine, on ajoute la contrainte sur le Mecredi
        for week in range(nbWeek):
            model += lpSum(x[i][week * 6 + j][k] for k in range(0, formationStopHourIndex)) == 0

#Here we force employee to start only 1 time (no gape between work hours)
start = LpVariable.dicts("start", (range(n), range(m), range(o)), cat=LpBinary)
for i in range(n):
    for j in range(m):

        #Force start to be equal to 1 if precedent hour is 0 and current is 1
        for k in range(o):
            if (k == 0):
                model += start[i][j][k] == x[i][j][k]
            else:
                #k - 1 doit valoir 0 et k doit valoir 1 pour que start soit contraint de valoir 1
                model += start[i][j][k] >= (1 - x[i][j][k-1]) + x[i][j][k] - 1
        
        #Constraint the sum of start for 1 day and 1 employee to be less or equal to 1
        model += lpSum(start[i][j][k] for k in range(o)) <= 1


### Regle de rush

#Il faut au moins une des personnes de atLeastOneIndex pendant le rush
if atLeastOneIndex:
    for j in range(m):
        for k in range(rushStartIndex, rushEndIndex):
            model += lpSum(x[i][j][k] for i in atLeastOneIndex) >= 1

#Impossible de commencer pendant le rush
for i in range(n):
    for j in range(m):
        model += lpSum(start[i][j][k] for k in range(rushStartIndex, rushEndIndex)) == 0

#Variable indiquant si on n'a pas encore rushNbOpti personnes pendant le rush
missingRush2 = LpVariable.dicts("missingRush2", (range(n), range(m), range(rushStartIndex, rushEndIndex)), cat=LpBinary)
for i in range(n):
    for j in range(m):
        for k in range(rushStartIndex, rushEndIndex):
            model += missingRush2[i][j][k] >= (rushNbOpti - x[i][j][k]) / rushNbOpti

# missingRush = LpVariable.dicts("missingRush", (range(m), range(rushStartIndex, rushEndIndex)), cat=LpBinary)
# for j in range(m):
#     for k in range(rushStartIndex, rushEndIndex):
#         model += missingRush[j][k] >= (rushNbOpti - lpSum(x[i][j][k] for i in range(n))) / rushNbOpti


#Objective
# model += lpSum(x[i][j][k] for i in range(n) for j in range(m) for k in range(o))
# model += lpSum(working[i][j] for i in range(n) for j in range(m)) / n
# model += 
model += lpSum(onePause[i][week] for i in range(n) for week in range(nbWeek)) * 100000 \
       + lpSum(tooLowDay[i][j] for i in range(n) for j in range(m)) / n * 100 \
       + lpSum(missingRush2[i][j][k] for i in range(n) for j in range(m) for k in range(rushStartIndex, rushEndIndex)) \
    #    + lpSum(missingRush[j][k] for j in range(m) for k in range(rushStartIndex, rushEndIndex)) #Pour essayer de ne manquer de personne pendant le rush
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

    for week in range(nbWeek):
        print(f"{pplName[i]}: weekNb={week}, nbPause: {onePause[i][week].value()}")

        for j in range(week * 6, (week + 1) * 6):
            print(f"Range: {j} = {working[i][j].value()}")

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


# for i in range(n):
for j in range(m):
    print(f"{j} : ", end="")
    for k in range(rushStartIndex, rushEndIndex):
        print(f"{k}={missingRush[j][k].value()}", end=" ")
    
    print(" ")

print(employeeHours)
visualize(employeeHours, pplName)