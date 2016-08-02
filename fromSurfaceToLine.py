##### !!!!!! Need to deal with closed curve
##### should deal with startTuplePoint instead of startPoint


import rhinoscriptsyntax as rs
import Rhino
import scriptcontext



################################   SEGMENTER   ################################




# The difficulty of this programs lies in the choice of the criteria to stop the loop.
# 3 criteria have been chosen:
     # A) angle between curve and segment at the start
     # B) angle between curve and segment at the end
     # C) curve deviation = distance between curve and segment OR distance between the middle of curve and middle of segment
     # D) width is the minimum length a segment can get.
# C is necessary when the curve is overlapping itself
# D is the width of the extrusion. It is necessary because it is useless to be more precise than the double of the extrusion width
# NOTE: D is a criteria that stop segmentation whereas A, B and C are criteria that keep going segmentation

# Return angle between the segment and the the line from start point to mid point
def startMiddleAngleCurve(curve, line):
    midPoint = rs.CurveMidPoint(curve)
    middleLine = rs.AddLine(rs.CurveStartPoint(curve), midPoint)
    angle = rs.Angle2(middleLine, line)
    rs.DeleteObject(middleLine)
    return angle[0]

# Return angle between the segment and the the line from mid point to start point
def endMiddleAngleCurve(curve, line):
    midPoint = rs.CurveMidPoint(curve)
    middleLine = rs.AddLine(midPoint, rs.CurveEndPoint(curve))
    angle = rs.Angle2(middleLine, line)
    rs.DeleteObject(middleLine)
    return angle[0]

# Curve deviation is the maximum distance between two curves
def firstSegmenter(curve, angleMax,deviationMax, width, segmentList):
    #Analyse of the curvature
    draftLine = rs.AddLine(rs.CurveStartPoint(curve), rs.CurveEndPoint(curve))
    if rs.CurveLength(curve) > width*2: # Criteria D
        curveDeviation = rs.CurveDeviation(curve,draftLine)
        if curveDeviation: #in case curveDeviation doesn't work, we use the distance midpoint of curve and midpoint of draftLine
            if curveDeviation[2] > deviationMax or abs(endMiddleAngleCurve(curve, draftLine)) > angleMax or abs(startMiddleAngleCurve(curve, draftLine)) > angleMax:
                rs.DeleteObject(draftLine)
                (curve1, curve2) = rs.SplitCurve(curve, rs.CurveClosestPoint(curve, rs.CurveMidPoint(curve)))
                segmentList = firstSegmenter(curve1, angleMax, deviationMax, width, segmentList)
                segmentList.append(rs.CurveEndPoint(curve1))
                segmentList = firstSegmenter(curve2, angleMax, deviationMax, width, segmentList)
                segmentList.append(rs.CurveEndPoint(curve2))
                return segmentList
            else: return segmentList
        elif rs.Distance(rs.CurveMidPoint(curve), rs.CurveMidPoint(draftLine)) > deviationMax or abs(endMiddleAngleCurve(curve, draftLine)) > angleMax or abs(startMiddleAngleCurve(curve, draftLine)) > angleMax:
            rs.DeleteObject(draftLine)
            param = rs.CurveClosestPoint(curve, midPoint) #Approximation
            (curve1, curve2) = rs.SplitCurve(curve, param)
            segmentList = firstSegmenter(curve1, angleMax, deviationMax, width, segmentList)
            segmentList.append(rs.CurveEndPoint(curve1))
            segmentList = firstSegmenter(curve2, angleMax, deviationMax, width, segmentList)
            segmentList.append(rs.CurveEndPoint(curve2))
            return segmentList
        else:
            return segmentList
    else:
        rs.DeleteObject(draftLine)
        return segmentList



def segmenter(curve, angleMax, deviationMax, width):
    segmentList = [rs.CurveStartPoint(curve)]
    
    segmentList = firstSegmenter(curve, angleMax,deviationMax, width, segmentList)
#    curvePointList = [rs.CurveStartPoint(segmentList[0])]
#    for i in range(0, len(segmentList)):
#        curvePointList.append(rs.CurveEndPoint(segmentList[i]))
#    return curvePointList



def test2():
    curve = rs.GetObject()
    segmenter(curve, 5, 5, 5)

test2()


################################   FROM SURFACE TO LINES   ################################

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
# If there's always interference whatever the point chosen, we just go for the shortest distance not to bother too much (see sortPointWithinLayer)
# curveList include startCurve
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
        if rs.CurveCurveIntersection(temporaryLine, curveList[i]) == None: # No overlap
            pass
        elif len(rs.CurveCurveIntersection(temporaryLine, curveList[i])) == 1: # 1 overlap
            if curveList[i] == startCurve or pointInCurve(endPoint, curveList[i]): #1) temporary line will always have at least 1 interesection with startCurve; 2) Same with the other curve
                pass
            else:
                bool = 1
        else: # 2+ overlap
            bool = 1
        i = i + 1
    return 1


# returns a sorted List of pointList and curveList according to the two criteria. It returns all the point of the layer but the last one
# Each iteration is a new curve
# !!!!!! With this method, the non extruded distance is not all the time the shortest one.
# !!! Need to deal with the case when the curve is a closed curve !!!
def sortPointsWithinLayer(startPoint, curveList, sortedCurveList, newTuplePointList): # Note: 1st iteration: newPointList = []
    pointList = [] #gather all points but the start tuple (if 2 surfaces then len = 2)
    for i in range(0, len(curveList)):
        iStartPoint = rs.CurveStartPoint(curveList[i])
        iEndPoint = rs.CurveEndPoint(curveList[i])
        # in the following conditions, we determine what the actual start point is, that is the point on the other side of the 1st curve to extrude
        # in the process we exclude this tuple from the newly created list
        if startPoint == iStartPoint:
            newTuplePointList.append([startPoint, iEndPoint]) #We add the first tuple to the result
            sortedCurveList.append(curveList[i]) # And we add the curve associated to that tuple
        elif startPoint == iEndPoint:
            newTuplePointList.append([startPoint, iStartPoint]) #We add the first tuple to the result
            sortedCurveList.append(curveList[i]) # And we add the curve associated to that tuple
        else:
            pointList.append(iStartPoint)
            pointList.append(iEndPoint)
    # let's determine the next point
    k = 0
    sortedPointList = shortestDistance(startPoint, pointList)
    while isOverlap(startPoint, sortedPointList[k], sortedCurveList[-1], curveList) and k < len(curveList) -1:
        k += 1
    
    if len(sortedCurveList) == len(curveList) - 1: # this was the last iteration
        return [newTuplePointList, sortedPointList[0], sortedCurveList]
    else: #if not last iteration
        if k == len(curveList): # if it interfers with any curve, nervermind, we go for the shortest distance otherwise it becomes too complicated
            [newTuplePointList, endPoint, sortedCurveList] = sortPointsWithinLayer(sortedPointList[0], curveList, sortedCurveList, newTuplePointList)
            return [newTuplePointList, endPoint, sortedCurveList]
        else:
            [newTuplePointList, endPoint, sortedCurveList] = sortPointsWithinLayer(sortedPointList[k], curveList, sortedCurveList, newTuplePointList)
            return [newTuplePointList, endPoint, sortedCurveList]


def test():
    curveList = []
    curveList.append(rs.GetObject())
    startPoint = rs.CurveStartPoint(curveList[0])
    curveList.append(rs.GetObject())
    [tuplePointList, endPoint, i0] = sortPointsWithinLayer(startPoint, curveList, [], [])
    print tuplePointList
    print endPoint
    
    
#test()

#  returns the other end point of a curve
def otherEndPoint(point, curve):
    if rs.CurveStartPoint(curve) == point:
        return rs.CurveEndPoint(curve)
    else:
        return rs.CurveStartPoint(curve)


# returns the closest point of layer (n+1) from endPoint of layer n.
# !!! Need to deal with the case when the curve is a closed curve !!!
def sortPointsBetweenLayers(point, tuplePointList):
    startPoint = tupleShortestDistance(point, tuplePointList)
    return startPoint


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


# returns the number of layers. Note: the curveList must be organized as follow:
# curveList[:] = curve of a surface
def numberOfLayersCalculation(curveList):
    return len(curveList)



# returns a full sorted pointList
# Recursive function. Initial value: layerNumber = 0, newPointList = [startPoint]
# Each iteration is a layer
# Note: sortPointWithinLayer returns all tuple points of a list sorted except the last one => 2 .append in this function:
    # - 1 with sortPointWithinLayer
    # - 1 with the last point
def fullSortedPointList(startPoint, curveList, objectTuplePointList, objectCurveList, layerNumber, numberOfLayers):
    layerNumber += 1
    # sortPointsWithinLayer returns all tuple points sorted of a list except the last one
    [layerTuplePointList, endPoint, sortedCurveList] = sortPointsWithinLayer(startPoint, curveList[layerNumber], [], [])
    objectTuplePointList[layerNumber] = layerTuplePointList
    objectCurveList.append(sortedCurveList)
    # Define and append the last tuple
    objectTuplePointList[layerNumber].append([ endPoint, otherEndPoint(endPoint, sortedCurveList[-1]) ])
    # Determine the next startPoint / only if there is a next layer
    if layerNumber == numberOfLayers - 1:
        return objectTuplePointList, objectCurveList, curveList, layerNumber, numberOfLayers
    else:
        tuplePointList = fromCurveListToTuplePointList(curveList[layerNumber + 1]) # temporary variable
        startPoint = sortPointsBetweenLayers(objectTuplePointList[layerNumber][-1][-1], tuplePointList) #End Point of last curve
        fullSortedPointList(startPoint, curveList, objectTuplePointList, objectCurveList, layerNumber, numberOfLayers)
        return objectTuplePointList, objectCurveList, curveList, layerNumber, numberOfLayers


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


def reorganisation(curvePointList, tuplePoint):
    newCurvePointList = []
    if curvePointList[0] == tuplePoint[0] and curvePointList[-1] == tuplePoint[-1]:
        return curvePointList
    if curvePointList[0] == tuplePoint[-1] and curvePointList[-1] == tuplePoint[0]:
        for i in range(1, len(curvePointList) + 1):
            newCurvePointList.append(curvePointList[-i])
        return newCurvePointList
    else:
        print 'NOOOOOO'
        return curvePointList


def main():
    # Input
    layerHeight = float(input("Layer Height?"))
    layerWidth = float(input("Layer Width?"))
    curveList = multipleSrf(layerHeight)
    
    # Initialization
    angleMax = 5
    deviationMax = 5
    numberOfLayers = numberOfLayersCalculation(curveList)
    initialTuplePointList = fromCurveListToTuplePointList(curveList[0])
    startPoint = tupleShortestDistance((0,0,0), initialTuplePointList) #startPoint is the closest to the origin (0,0,0)
    objectTuplePointList = []
    objectCurveList = []
    for i in range(0, numberOfLayers):
        objectTuplePointList.append([])
    voxeledStep = []
    voxeledGCode = []
    
    # Algorithm
    result = fullSortedPointList(startPoint, curveList, objectTuplePointList, objectCurveList, -1, numberOfLayers)
    objectTuplePointList = result[0]
    objectCurveList = result[1]
    
    # Segmentation + voxeled GCode
    for layerNumber in range(0, len(curveList)): #For each layer of 1 object
        for curveNumber in range(0, len(curveList[layerNumber])): # For each curve of 1 layer
            curvePointList = segmenter(curveList[layerNumber][curveNumber], angleMax, deviationMax, layerWidth)
            curvePointList = reorganisation(curvePointList, objectTuplePointList[layerNumber][curveNumber])
            for point in range(0, len(curvePointList) - 1): # For each segment of 1 curve
                voxeledStep.append("G1")
                a = curvePointList[point]
                voxeledStep.append(curvePointList[point][2])
                voxeledStep.append(curvePointList[point][0])
                voxeledStep.append(curvePointList[point][1])
                voxeledStep.append(999999999)
                voxeledStep.append(999999999)
                voxeledGCode.append(voxeledStep)
            voxeledStep.append("G1")
            voxeledStep.append(curvePointList[point][2])
            voxeledStep.append(curvePointList[point][0])
            voxeledStep.append(curvePointList[point][1])
            voxeledStep.append(0)
            voxeledStep.append(999999999)
            voxeledGCode.append(voxeledStep)
    
    # Unvoxeled GCode



#    for i in range(0, len(curveList)):
#        layerPointList.append(pointList) #This is a list of a list of a list of points (a list of a list of curves ; a list of layers since layers = list of curves)
#        for j in range(0, len(curveList[i]):
#            segmentPointList = segmenter(curveList[i][j], 5, 5, layerWidth #by default deviationmax = 5 and anglemax = 5 ; this is a pointList of the segments
#            curvePointList.append(segmentPointList): #This is a list of a list of points (list of curves)

#main()

def checkSamePoint(voxeledGCode):
    for i in range(voxeledGCode):
        for j in range(voxeledGCode):
            if voxeledGCode[i][2] == voxeledGCode[j][2]:
                return 1
    return 0