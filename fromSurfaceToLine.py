##### !!!!!! Need to deal with closed curve


import rhinoscriptsyntax as rs
import Rhino
import scriptcontext
from Segmenter import *

# Firstly we split the surface 1 by 1
# Then we join the curves together

# It is easy to join the curve when there are just 2 surfaces (There are only 2 combinations)
# It is harder when there are more than 2 surfaces
# We need to set up some criteria to determinate the order of the junction
# 2 criteria:
    # - Quantity criteria: length travelled between the two curves
    # - Condition criteria: avoid overlapping


def fromSurfaceToLine(layerHeight, srf):
    BB = rs.BoundingBox(srf)
    height = float(BB[6][2] - BB[0][2])
    numberOfLayers = int(height / layerHeight) + 1
    curveList = []
    for i in range(0, numberOfLayers):
        corner1 = str(BB[0][0]) + "," + str(BB[0][1]) + "," + str(BB[0][2] + i*layerHeight )
        corner2 = str(BB[2][0]) + "," + str(BB[2][1]) + "," + str(BB[2][2] + i )
        rs.Command("-plane " + corner1 + " " + corner2 + " " )
        layer = rs.LastCreatedObjects()
        rs.UnselectAllObjects()
        rs.SelectObject(layer[0])
        rs.SelectObject(srf)
        rs.Command("intersect ")
        rs.DeleteObject(layer)
        curveList.append(rs.LastCreatedObjects()[0])
    return (curveList)


# returns a sorted list according to the distance from 1 point
# This function has to be used from the end point of the start curve to the start point of the end curve
# Start Curve is the first extruded curve of the layer and is determined by another algorithm (interlayer algorithm)
# So pointList = point within a layer - point attached to ref point by a curve
def shortestDistance(point, pointList):
    newPointList = []
    distanceList = []
    for i in range(0, len(pointList)):
        distanceList.append(rs.Distance(point, pointList[i]))
    jRange = len(pointList)
    for j in range(0, jRange):
        newPointList.append(pointList[ distanceList.index(min(distanceList)) ])
        pointList.remove(pointList[ distanceList.index(min(distanceList)) ])
        distanceList.remove(min(distanceList))
    return newPointList


# returns same as above, but with a tuplePoint list as a input
def tupleShortestDistance(point, tuplePointList):
    A = tuplePointList[:][0]
    pointA =  shortestDistance(point, tuplePointList[:][0])[0]
    pointB =  shortestDistance(point, tuplePointList[:][1])[0]
    return shortestDistance(point, [pointA, pointB])[0]


# Returns 1 in a point is part of a curve, 0 if not
def pointInCurve(point, curve):
    if point == rs.CurveStartPoint(curve) or point == rs.CurveEndPoint(curve):
        return 1
    else:
        return 0



# returns a boolean for whether or not the part to the new point selected interfers with one the curve:
     # - 1 if it interferes
     # - 0 if not
# If it does, we just choose another point. 
# If there's always interference whatever the point chosen, we just go for the shortest distance not to bother too much.
def isOverlap(startPoint, endPoint, startCurve, curveList):
    temporaryLine = rs.AddLine(startPoint, endPoint)
    i = 0
    bool = 0
    while bool == 0:
        # Once we have done all the curves, time to say there is no overlap whatsoever
        if i == len(curveList):
            rs.DeleteObject(temporaryLine)
            return 0
        # below are all the cases that we can encounter
        if rs.CurveCurveIntersection(temporaryLine, curveList[i]) == None:
            pass
        elif len(rs.CurveCurveIntersection(temporaryLine, curveList[i])) == 1:
            if curveList[i] == startCurve or pointInCurve(endPoint, curveList[i]):
                pass
            else:
                bool = 1
        else:
            bool = 1
        i = i + 1
    return 1


# returns a sorted List of pointList and curveList according to the two criteria
# Each iteration is a new curve
# !!!!!! With this method, the non extruded distance is not all the time the shortest one.
# !!! Need to deal with the case when the curve is a closed curve !!!
def sortPointsWithinLayer(startPoint, curveList, newTuplePointList, i0): # Note: 1st iteration: limit = len(curveList) - 1 and newPointList =[]
    lastIt = len(curveList)
    pointList = []
    newCurveList = []
    for i in range(0, len(curveList)):
        iStartPoint = rs.CurveStartPoint(curveList[i])
        iEndPoint = rs.CurveEndPoint(curveList[i])
        # in the following conditions, we determine what the actual start point is, that is the point on the other side of the 1st curve to extrude
        # in the process we exclude this tuple from the newly created list
        if startPoint == iStartPoint:
            newTuplePointList.append([startPoint, iEndPoint]) #We add the first tuple to the result
            i0.append(i)
        elif startPoint == iEndPoint:
            newTuplePointList.append([startPoint, iStartPoint]) #We add the first tuple to the result
            i0.append(i)
        else:
            pointList.append(iStartPoint)
            pointList.append(iEndPoint)
            newCurveList.append(curveList[i])
    # let's determine the next point
    k = 0
    sortedPointList = shortestDistance(startPoint, pointList)
    while isOverlap(startPoint, sortedPointList[k], curveList[i0[-1]], newCurveList) and k < len(newCurveList):
        k += 1
    
    if len(newCurveList) == 1: # this was the last iteration
        return [newTuplePointList, sortedPointList[0], i0]
    else: #if not last iteration
        if k == len(newCurveList): # if it interfers with any curve, nervermind, we go for the shortest distance otherwise it becomes too complicated
            [newTuplePointList, endPoint, i0] = sortPointsWithinLayer(sortedPointList[0], newCurveList, newTuplePointList, i0)
            return [newTuplePointList, endPoint, i0]
        else:
            [newTuplePointList, endPoint, i0] = sortPointsWithinLayer(sortedPointList[k], newCurveList, newTuplePointList, i0)
            return [newTuplePointList, endPoint, i0]


# re-organise the list curveList according to an established order i0
def listReorganisation(curveList, i0):
    newCurveList = []
    for i in range(0, len(curveList)):
        newCurveList.append(curveList[i0[i]])
    return newCurveList


#  returns the other end point of a curve
def otherEndPoint(point, curve):
    if rs.CurveStartPoint(curve) == point:
        return rs.CurveEndPoint(curve)
    else:
        return rs.CurveStartPoint(curve)


def test():
    curveList = []
    curveList.append(rs.GetObject())
    startPoint = rs.CurveStartPoint(curveList[0])
    curveList.append(rs.GetObject())
    curveList.append(rs.GetObject())
    limit = len(curveList) - 1
    [tuplePointList, endPoint] = sortPointsWithinLayer(startPoint, curveList, [], [])
    print tuplePointList
    print endPoint
    
    
#test()


# returns the closest point of layer (n+1) from endPoint of layer n.
# !!! Need to deal with the case when the curve is a closed curve !!!
def sortPointsBetweenLayers(point, tuplePointList):
    sortedPointList = tupleShortestDistance(point, tuplePointList)
    return sortedPointList[0]


def selectSurfaces():
    srf = []
    while True:
        objectId = rs.GetObject("Select the surfaces", 8)
        if not(objectId):
            break
        srf.append(objectId)
    return srf


# returns a pointList made out of tuples (startPoint and endPoint of curves)
def fromCurveListToTuplePointList(curveList):
    tuplePointList = []
    for i in range(0,len(curveList)):
        tuplePoint = [ rs.CurveStartPoint(curveList[i]), rs.CurveEndPoint(curveList[i]) ]
        tuplePointList.append( tuplePoint)
    return tuplePointList


def multipleSrf(layerHeight):
    rs.UnselectAllObjects()
    srf = []
    i = 0
    listOfNumberOfLayers = [0]
    curveList = []
    newCurveList = []
    layerCurveList = []
    
    srf = selectSurfaces()
    
    numberOfSurfaces = len(srf)
    for p in range(0, numberOfSurfaces):
        curveList.append(fromSurfaceToLine(layerHeight, srf[p]))
    
    #re-organization of the list of curve
    for j in range( 0, max(len(curveList[k]) for k in range(0, numberOfSurfaces)) ):
        for i in range(0, numberOfSurfaces):
            try:
                newCurveList.append(curveList[i][j])
            except:
                pass
        layerCurveList.append(newCurveList)
        newCurveList = []
    return layerCurveList


# returns a full sorted pointList
# Recursive function. Initial value: layerNumber = 0, newPointList = [startPoint]
# Each iteration is a layer
def fullSortedPointList(startPoint, curveList, newPointList, layerNumber):
    tuplePointList = fromCurveListToTuplePointList(curveList[layerNumber])
    newPointList.append( sortPointsWithinLayer(startPoint, curveList[layerNumber], [], len(curveList[layerNumber]) - 1) )
    [newTuplePointList, endPoint, i0] = sortPointsBetweenLayers(newPointList[-1][-1][-1], tuplePointList)
    sortedCurveList = listReorganisation(curveList[layerNumber], i0)
    startPoint = otherEndPoint(point, sortedCurveList)
    
    fullSortedPointList(startPoint, curveList, newPointList, layerNumber + 1)
    
    return curveList, newPointList, layerNumber

def main():
    layerHeight = float(input("Layer Height?"))
    layerWidth = float(input("Layer Width?"))
    curveList = multipleSrf(layerHeight)
    
    initialTuplePointList = fromCurveListToTuplePointList(curveList[0])
    startPoint = tupleShortestDistance((0,0,0), initialTuplePointList) #startPoint is the closest to the origin (0,0,0)
    
    sortedPointList = fullSortedPointList(startPoint, curveList, [], 0)[1]
    print sortedPointList[0]


#    for i in range(0, len(curveList)):
#        layerPointList.append(pointList) #This is a list of a list of a list of points (a list of a list of curves ; a list of layers since layers = list of curves)
#        for j in range(0, len(curveList[i]):
#            segmentPointList = segmenter(curveList[i][j], 5, 5, layerWidth #by default deviationmax = 5 and anglemax = 5 ; this is a pointList of the segments
#            curvePointList.append(segmentPointList): #This is a list of a list of points (list of curves)

main()