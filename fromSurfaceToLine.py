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

def joinCurves(listOfNumberOfLayers, listOfPointList, numberOfSurfaces):

    # Do connections within layers
    for l in range(0, numberOfSurfaces):
        for j in range(listOfNumberOfLayers[l], listOfNumberOfLayers[l + 1]):
            if j % 2 == 0:
                for q in range(l + 1, numberOfSurfaces):
                    startPoint = listOfPointList [q - 1] [j] [1]
                    endPoint = listOfPointList [q] [j] [0]
                    rs.Command("-line " + str(startPoint) + " " + str(endPoint) + " " )
            elif j % 2 == 1:
                for q in range(l + 1, numberOfSurfaces):
                    startPoint = listOfPointList [q] [j] [0]
                    endPoint = listOfPointList [q - 1] [j] [1]
                    rs.Command("-line " + str(startPoint) + " " + str(endPoint) + " " )
            else:
                pass
            
    # Do connections between layers
    for o in range(0, numberOfSurfaces):
        for k in range(listOfNumberOfLayers[o], listOfNumberOfLayers[o + 1] - 1):
            if k % 2 == 0:
                startPoint = listOfPointList [numberOfSurfaces - 1] [k] [1]
                endPoint = listOfPointList [numberOfSurfaces - 1] [k + 1] [1]
                rs.Command("-line " + str(startPoint) + " " + str(endPoint) + " " )
            elif k % 2 == 1:
                startPoint = listOfPointList [o] [k] [0]
                endPoint = listOfPointList [o] [k + 1] [0]
                rs.Command("-line " + str(startPoint) + " " + str(endPoint) + " " )
            else:
                pass

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

#returns a sorted List of pointList and curveList according to the two criteria
# !!!!!! With this method, the non extruded distance is not all the time the shortest one.
def sortPointsWithinLayer(startPoint, curveList, newPointList, limit): # Note: 1st iteration: limit = limit = len(curveList)*2 - 1 and newPointList =[]
    newPointList.append(startPoint) #we add the to result the first point
    pointList = []
    newCurveList = []
    for i in range(0, len(curveList)):
        iStartPoint = rs.CurveStartPoint(curveList[i])
        iEndPoint = rs.CurveEndPoint(curveList[i])
        # in the following conditions, we determine what the actual start point is, that is the point on the other side of the 1st curve to extrude
        # in the process we exclude this tuple from the newly created list
        if startPoint == iStartPoint:
            startPoint = iEndPoint
            newPointList.append(startPoint) #we add to the result the other point
            i0 = i
        elif startPoint == iEndPoint:
            startPoint = iStartPoint
            newPointList.append(startPoint) #we add to the result the other point
            i0 = i
        else:
            pointList.append(iStartPoint)
            pointList.append(iEndPoint)
            newCurveList.append(curveList[i])
    # let's determine the next point
    k = 0
    sortedPointList = shortestDistance(startPoint, pointList)
    while isOverlap(startPoint, sortedPointList[k], curveList[i0], newCurveList) and k < len(newCurveList):
        k += 1
    if k == len(newCurveList): # if it interfers with any curve, nervermind, we go for the shortest distance otherwise it becomes too complicated
        if len(newPointList) == limit - 1: # -1 because we didn't add the third point (will be done next step)
            return newPointList
        else:
            newPointList = sortPointsWithinLayer(sortedPointList[0], newCurveList, newPointList, limit)
    else:
        if len(newPointList) == limit - 1: # -1 because we didn't add the third point (will be done next step)
            return newPointList
        else:
            newP0ointList = sortPointsWithinLayer(sortedPointList[k], newCurveList, newPointList, limit)

def sortPointsBetweenLayers(point, curveList, pointList):
    sortedPointList = shortestDistance(point, pointList)
    if point[0] == sortedPointList[0][0] and point[1] == sortedPointList[0][0]:
        return 0


def selectSurfaces():
    srf = []
    while True:
        objectId = rs.GetObject("Select the surfaces", 8)
        if not(objectId):
            break
        srf.append(objectId)
    return srf

def multipleSrf(layerHeight):
    rs.UnselectAllObjects()
    srf = []
    i = 0
    listOfNumberOfLayers = [0]
    curveList = []
    newCurveList = []
    
    srf = selectSurfaces()
    
    numberOfSurfaces = len(srf)
    for p in range(0, numberOfSurfaces):
        curveList.append(fromSurfaceToLine(layerHeight, srf[p]))
    
    #re-organization of the list of curve
    for j in range(0, numberOfSurfaces):
        for i in range(0, len(curveList[j])):
            newCurveList.append(curveList[j][i])
    return newCurveList



#def main():
    

multipleSrf(10)