
from openpyxl import load_workbook


dayToIndex = {"Lundi":0, "Mardi":1, "Mercredi":2, "Jeudi":3, "Vendredi":4, "Samedi": 5}

#Nombre d'employee minimum par demi heure
#  0    1    2     3     4     5     6     7     8     9     10   11    12     13    14   15    16
hoursToIndex = {"8h30":0, "9h":1, "9h30":2, "10h":3, "10h30":4, "11h":5, "11h30":6, "12h":7,
                "12h30":8, "13h":9, "13h30":10, "14h":11, "14h30":12, "15h":13, "15h30":14,
                "16h":15, "16h30":16, "17h":17, "17h30":18, "18h":19, "18h30":20, "19h":21, "19h30":22}

def stringToDate(dateString):
    if dateString is None:
        return []
    
    ret = []
    for date in dateString.split(','):
        ret.append([])
        datePair = date.strip().split(' ')
        if len(datePair) < 2:
            print("Erreur de format de date :", dateString)

        ret[-1].append(dayToIndex[datePair[0]])
        for hour in datePair[1:]:
            ret[-1].append(hoursToIndex[hour.lower()])

    return ret
        

def readFile(fileName):

    wb = load_workbook(filename = fileName)
    data = wb.active

    #Get name row
    pplName = [name.value for name in data['1'][1:]]
    pplWeekHours = [name.value for name in data['2'][1:]]
    maxHalfHoursPerDay = [9 if hour <= 20 else 11 for hour in pplWeekHours]

    inFormation = [name.value == 'Oui' for name in data['3'][1:]]
    startHour = [hoursToIndex[name.value] for name in data['4'][1:]]
    shoudlForceSunday = [name.value == 'Oui' for name in data['5'][1:]]
    needStartEarly = [name.value == 'Oui' for name in data['6'][1:]] 
    needStartLate = [name.value == 'Oui' for name in data['7'][1:]]
    endBefore = [stringToDate(name.value) for name in data['8'][1:]]
    absentRange = [stringToDate(name.value) for name in data['9'][1:]]

    return pplName, pplWeekHours, maxHalfHoursPerDay, inFormation, startHour, shoudlForceSunday, needStartEarly, needStartLate, endBefore, absentRange
