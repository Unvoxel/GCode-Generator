import rhinoscriptsyntax as rs
import Rhino

# The difficulty of this programs lies in the choice of the criteria to stop the loop.
# 3 criteria have been chosen:
     # A) angle between curve and segment at the start
     # B) angle between curve and segment at the end
     # C) angle between two consecutive segments
     # D) curve deviation = distance between curve and segment.
     # E) width is the minimum length a segment can get.
# D is necessary when the curve is overlapping itself
# E is the width of the extrusion. It is necessary because it is useless to be more
# precise than the double of the extrusion width
# We could have just used criteria E but it is not relevant to segment straight lines (for example)

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
def firstSegmenter(curve, lineList, curveList, angleMax,deviationMax, width):
    midPoint = rs.CurveMidPoint(curve)
    line1 = rs.AddLine(rs.CurveStartPoint(curve), midPoint)
    line2 = rs.AddLine(midPoint, rs.CurveEndPoint(curve))
    lineList.append(line1)
    lineList.append(line2)
    
    angleTuple = rs.Angle2(line1, line2) #Angle2 = return angle between 2 lines
    angle = angleTuple[0] #getting the angle in  degrees
    
    
    param = rs.CurveClosestPoint(curve, midPoint) #Approximation
    (curve1, curve2) = rs.SplitCurve(curve, param)
    
    print abs(angle)
    print abs(endMiddleAngleCurve(curve1, line1))
    print abs(startMiddleAngleCurve(curve1, line1))
    
    curveList.append(curve1)
    curveList.append(curve2)
    if rs.CurveLength(curve1) > width*2: # Criteria E
        curveDeviation = rs.CurveDeviation(curve1, line1)
        if curveDeviation: #curvedeviation doesn't work all the time (ie if no overlap distance is found)
            if curveDeviation[2] > deviationMax: # Criteria D, [2] = maximum overlap distance
                rs.DeleteObject(line1)
                lineList.remove(line1)
                curveList.remove(curve1)
                firstSegmenter(curve1, lineList, curveList, angleMax,deviationMax, width)
        elif abs(angle) > angleMax or abs(endMiddleAngleCurve(curve1, line1)) > angleMax or abs(startMiddleAngleCurve(curve1, line1)) > angleMax:
            rs.DeleteObject(line1)
            lineList.remove(line1)
            curveList.remove(curve1)
            firstSegmenter(curve1, lineList, curveList, angleMax,deviationMax, width)
                
    if rs.CurveLength(curve2) > width*2:
        curveDeviation = rs.CurveDeviation(curve2, line2)
        if curveDeviation:
            if curveDeviation[2] > deviationMax:
                rs.DeleteObject(line2)
                lineList.remove(line2)
                curveList.remove(curve2)
                firstSegmenter(curve2, lineList, curveList, angleMax,deviationMax, width)
        elif abs(angle) > angleMax or abs(endMiddleAngleCurve(curve2, line2)) > angleMax or abs(startMiddleAngleCurve(curve2, line2)) > angleMax:
            rs.DeleteObject(line2)
            lineList.remove(line2)
            curveList.remove(curve2)
            firstSegmenter(curve2, lineList, curveList, angleMax,deviationMax, width)
            
    numberOfSegments = len(lineList)
    return (lineList, curveList, numberOfSegments)

def Segmenter(angleMax, deviationMax, width):
    curve = rs.SelectedObjects()
    lineList = []
    curveList = []
    
    (lineList, curveList, numberOfSegments) = firstSegmenter(curve, lineList, curveList, angleMax,deviationMax, width)
    
    rs.JoinCurves(curveList, True)
    result = rs.JoinCurves(lineList, True)
    return result

Segmenter(5, 5, 5)