

def convert2dDayAndHours(array2D, matchingDayMap, matchingHourMap):

    rez = []

    for array in array2D:
        rez.append([])

        for elem in array:
            rez[-1].append([])

            rez[-1][-1].append(matchingDayMap[elem[0]])

            for hour in elem[1:]:
                rez[-1][-1].append(matchingHourMap[hour])

    return rez
