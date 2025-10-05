import sqlite3
import datetime
import matplotlib.pyplot as plt
from pandas import Series

def cell_1():
    fig = plt.figure(figsize=(9, 6))
    return fig

def cell_2():
    siteID = '3'
    siteName = 'Logan River at Main Street (Highway 89/91) Bridge'
    variableID1 = '9'
    variableID2 = '15'
    startDateTime = "'2016-01-01'"
    endDateTime = "'2016-12-31'"
    return siteID, variableID1, startDateTime, endDateTime

def cell_3(siteID, variableID1, startDateTime, endDateTime):
    conn = sqlite3.connect('cee6440_ex3_loganriver.sqlite')
    sql_statement1 = 'SELECT LocalDateTime, DataValue ' \
                    'FROM DataValues ' \
                    'WHERE SiteID = ' + siteID + ' AND VariableID = ' + variableID1 + \
                    ' AND LocalDateTime >= ' + startDateTime + ' AND LocalDateTime < ' + endDateTime + \
                    ' AND QualityControlLevelID = 1 ' \
                    'AND DataValue <> -9999 ' \
                    'ORDER BY LocalDateTime'
    cursor = conn.cursor()
    cursor.execute(sql_statement1)
    rows = cursor.fetchall()
    localDateTimes1, dataValues1 = zip(*rows)
    return localDateTimes1, dataValues1

def cell_4(localDateTimes1):
    plotDates1 = []
    for x in localDateTimes1:
        plotDates1.append(datetime.datetime.strptime(x, '%Y-%m-%d %H:%M:%S'))
    return plotDates1

def cell_5(dataValues1, plotDates1):
    ts = Series(dataValues1, index=plotDates1)
    return ts

def cell_6(ts):
    ####### Alteracao feita com base nesta resposta do StackOverflow https://stackoverflow.com/questions/23162472/python-pandas-daily-average
    #######dailyAvg = ts.resample(rule='1D', base=0).mean() 
    dailyAvg = ts.resample(rule='1D').agg("mean")
    return dailyAvg

def cell_7(fig, dailyAvg):
    # Add the first subplot to the figure
    ax = fig.add_subplot(1, 1, 1)  # (rows, columns, specific subplot assigned to ax)


    # Plot the timeseries data
    dailyAvg.plot(color='red')


    # Set properties of the first subplot
    plt.ylabel("Turbidity (NTU)", color='red')
    plt.xlabel("Date")
    plt.yticks(color='red')
    plt.grid(axis='y')
    plt.title("Average Daily Turbidity on the Logan River at Mendon Rd in 2016")


    # Rotate the x-axis labels so they don't overlap and use matplotlib's
    # automated tight layout function to arrange layout
    plt.xticks(rotation=30)
    fig.tight_layout()

    # Display Plot
    plt.savefig("out.png")

def main():
    fig = cell_1()
    siteID, variableID1, startDateTime, endDateTime = cell_2()
    localDateTimes1, dataValues1 = cell_3(siteID, variableID1, startDateTime, endDateTime)
    plotDates1 = cell_4(localDateTimes1)
    ts = cell_5(dataValues1, plotDates1)
    dailyAvg = cell_6(ts)
    cell_7(fig, dailyAvg)

import time
start = time.perf_counter()
main()
print(str(time.perf_counter()-start).replace(".",","))