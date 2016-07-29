import rhinoscriptsyntax as rs
import Rhino

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
    sectionId = []
    pointList = []
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
        sectionId = rs.LastCreatedObjects()
        point = [rs.CurveStartPoint(sectionId[0]), rs.CurveEndPoint(sectionId[0])]
        pointList.append( point )
    return (numberOfLayers, pointList)

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

# returns a boolean for whether or not the part to the new point selected interfers with one the curve:
     # - 0 if it interferes
     # - 1 if not
# If it does, we just choose another point. 
# If there's always interference whatever the point chosen, we just go for the shortest distance not to bother too much.
def overlappingPointList(startPoint, endPoint, curveList):
    temporaryLine = rs.AddLine(startPoint, endPoint)
    rs.UnselectAllObjects()
    i = 0
    bool = 0
    while bool == 0:
        if i == len(curveList):
            return 1
        rs.SelectObjects([temporaryLine, curveList[i]])
        rs.Command("intersect ")
        if rs.IsPoint(rs.UnselectObject(curveList[i])):
            bool = 1
        rs.UnselectObject(curveList[i])
        i = i + 1
    return 0

#returns a sorted List of pointList and curveList according to the two criteria
# !!!!!! With this method, the non extruded distance is not all the time the shortest one.
def sortLayer2(startPoint, curveList, newPointList, limit):
    
    pointList = []
    newCurveList = []
    for i in range(0, len(curveList)):
        iStartPoint = rs.CurveStartPoint(curveList[i])
        iEndPoint = rs.CurveEndPoint(curveList[i])
        # in the following conditions, we determine what the actual start point is, that is the point on the other side of the 1st curve to extrude
        # in the process we exclude this tuple from the newly created list
        if startPoint == iStartPoint:
            startPoint = iEndPoint
        elif startPoint == iEndPoint:
            startPoint = iStartPoint
        else:
            pointList.append(iStartPoint)
            pointList.append(iEndPoint)
            newCurveList.append(curveList[i])
    # let's determine the next point
    k = 0
    sortedPointList = shortestDistance(startPoint, pointList)
    while overlappingPointList(startPoint, sortedPointList[k], newCurveList):
        k += 1
    if k > len(sortedPointList): # if it interfers with any curve, nervermind, we go for the shortest distance otherwise it becomes too complicated
        newPointList.append(sortedPointList[0])
        if len(newPointList) == limit:
            return newPointList
        else:
            newPointList = sortLayer2(sortedPointList[0], newCurveList, newPointList, limit)
    else:
        newPointList.append(sortedPointList[k])
        if len(newPointList) == limit:
            return newPointList
        else:
            newPointList = sortLayer2(sortedPointList[k], newCurveList, newPointList, limit)


def sortLayer(startPoint, curveList, newPointList, limit):
    
    pointList = []
    newCurveList = []
    for i in range(0, len(curveList)):
        iStartPoint = rs.CurveStartPoint(curveList[i])
        iEndPoint = rs.CurveEndPoint(curveList[i])
        # in the following conditions, we determine what the actual start point is, that is the point on the other side of the 1st curve to extrude
        # in the process we exclude this tuple from the newly created list
        if startPoint == iStartPoint:
            startPoint = iEndPoint
        elif startPoint == iEndPoint:
            startPoint = iStartPoint
        else:
            pointList.append(iStartPoint)
            pointList.append(iEndPoint)
            newCurveList.append(curveList[i])
    # let's determine the next point
    k = 0
    sortedPointList = shortestDistance(startPoint, pointList)
    while overlappingPointList(startPoint, sortedPointList[k], newCurveList):
        k += 1
    if k > len(sortedPointList): # if it interfers with any curve, nervermind, we go for the shortest distance otherwise it becomes too complicated
        newPointList.append(sortedPointList[0])
        if len(newPointList) == limit:
            return newPointList
        else:
            newPointList = sortLayer2(sortedPointList[0], newCurveList, newPointList, limit)
    else:
        newPointList.append(sortedPointList[k])
        if len(newPointList) == limit:
            return newPointList
        else:
            newPointList = sortLayer2(sortedPointList[k], newCurveList, newPointList, limit)

def sortLayer1():
    startPoint = rs.GetObject()
    startPoint = rs.PointCoordinates(startPoint)
    curveList = []
    curveList.append(rs.GetObject())
    curveList.append(rs.GetObject())
    curveList.append(rs.GetObject())
    
    limit = len(curveList) - 1
    
    newPointList = []
    pointList = []
    newCurveList = []
    for i in range(0, len(curveList)):
        iStartPoint = rs.CurveStartPoint(curveList[i])
        iEndPoint = rs.CurveEndPoint(curveList[i])
        # in the following conditions, we determine what the actual start point is, that is the point on the other side of the 1st curve to extrude
        # in the process we exclude this tuple from the newly created list
        if startPoint == iStartPoint:
            startPoint = iEndPoint
        elif startPoint == iEndPoint:
            startPoint = iStartPoint
        else:
            pointList.append(iStartPoint)
            pointList.append(iEndPoint)
            newCurveList.append(curveList[i])
    # let's determine the next point
    k = 0
    sortedPointList = shortestDistance(startPoint, pointList)
    while overlappingPointList(startPoint, sortedPointList[k], newCurveList):
        k += 1
    if k > len(sortedPointList): # if it interfers with any curve, nervermind, we go for the shortest distance otherwise it becomes too complicated
        newPointList.append(sortedPointList[0])
        if len(newPointList) == limit:
            return newPointList
        else:
            newPointList = sortLayer(sortedPointList[0], newCurveList, newPointList, limit)
    else:
        newPointList.append(sortedPointList[k])
        if len(newPointList) == limit:
            return newPointList
        else:
            newPointList = sortLayer(sortedPointList[k], newCurveList, newPointList, limit)

print sortLayer1()

def selectSurfaces():
    srf = []
    while True:
        objectId = rs.GetObject("Select the surfaces in the right order", 8)
        if not(objectId):
            break
        srf.append(objectId)
    return srf

def multipleSrf(layerHeight):
    rs.UnselectAllObjects()
    srf = []
    i = 0
    listOfPointList = []
    listOfNumberOfLayers = [0]
    
    srf = selectSurfaces()
    
    numberOfSurfaces = len(srf)
    for p in range(0, numberOfSurfaces):
        (A,B) = fromSurfaceToLine(layerHeight, srf[p])
        listOfNumberOfLayers.append( A )
        listOfPointList.append( B )
    
    joinCurves(listOfNumberOfLayers, listOfPointList, numberOfSurfaces)

#multipleSrf(100)