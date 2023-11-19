from datetime import datetime

from processing.data import Data
from processing.utils.nexrad_stations import _radar_stations as station_list


def numeric(tokens):
    num = ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9')
    for item in tokens:
        for char in item:
            if char not in num:
                return False
    return True

def valid_date(input):

    tokens = input.split(':')
    if (len(tokens) != 5) or (len(tokens[0]) != 4) or (not numeric(tokens)):
        return False, None
    date = None
    try:
        date = datetime(year=int(tokens[0]), month=int(tokens[1]), day=int(tokens[2]), hour=int(tokens[3]),
                         minute=int(tokens[4]))
    except:
        return False, date

    return True, date


if __name__ == "__main__":

    stations = []

    user = input(
        "\n\n\nPlease enter desired stations for analysis. List them in the 4 character NEXRAD code format, and end station input with '*', or enter 'all' to process all NEXRAD stations.\n\n").upper()
    while user != '*':

        if user in station_list:
            stations.append(user)
        elif user == 'ALL':
            stations = station_list
            break
        else:
            print("Error: Invalid station entered. Please enter next station or end list with '*': ")

        user = input().upper()

    if len(stations) == 0:
        print("No stations selected. Terminating Interface.")
        exit(0)

    print(stations)

    user = input("\n\nPlease enter desired start datetime of scan. Enter in the following format: YYYY:MM:DD:HH:MM\n")
    valid, start = valid_date(user)
    while not valid:
        user = input("Invalid input. Please enter start datetime in the following format: YYYY:MM:DD:HH:MM:\n")
        valid, start = valid_date(user)


    user = input("\n\nPlease enter desired end datetime of scan. Enter in the following format: YYYY:MM:DD:HH:MM\n")
    valid, end = valid_date(user)
    while not valid:
        user = input("Invalid input. Please enter end datetime in the following format: YYYY:MM:DD:HH:MM:\n")
        valid, end = valid_date(user)


    user = input("\n\nWould you like to include Hail Size Discrimination Analysis in the processing? (y/n)\n")
    while user not in ('y', 'n'):
        user = input(
            "\nInvalid entry. Would you like to include Hail Size Discrimination Analysis in the processing? (y/n)\n")

    HSDA = True if (user == 'y') else False

    print(
        "\n\nBeginning data download and processing for the following datetime range: {} - {}\nFor the following stations:\n{}\n\n".format(
            start, end, stations))

    processing_loop = Data(start, end, stations=stations, HSDA=HSDA)
