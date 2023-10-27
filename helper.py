

def convert2dWeekDayAndHours(array2D, matchingDayMap, matchingHourMap):

    rez = []

    for array in array2D:
        rez.append([])

        for elem in array:
            rez[-1].append([])

            rez[-1][-1].append(int(elem[0]) - 1)
            rez[-1][-1].append(matchingDayMap[elem[1]])

            for hour in elem[2:]:
                rez[-1][-1].append(matchingHourMap[hour])

    return rez
