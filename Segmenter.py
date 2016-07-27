import rhinoscriptsyntax as rs
import Rhino

def startMiddleAngleCurve(curve, line):
    midPoint = rs.CurveMidPoint(curve)
    middleLine = rs.AddLine(rs.CurveStartPoint(curve), midPoint)
    angle = rs.Angle2(middleLine, line)
    rs.DeleteObject(middleLine)
    return angle[0]



def endMiddleAngleCurve(curve, line):
    midPoint = rs.CurveMidPoint(curve)
    middleLine = rs.AddLine(midPoint, rs.CurveEndPoint(curve))
    angle = rs.Angle2(middleLine, line)
    rs.DeleteObject(middleLine)
    return angle[0]

def firstSegmenter(curve, lineList, curveList, angleMax,deviationMax, width):
    
    midPoint = rs.CurveMidPoint(curve)
    line1 = rs.AddLine(rs.CurveStartPoint(curve), midPoint)
    line2 = rs.AddLine(midPoint, rs.CurveEndPoint(curve))
    lineList.append(line1)
    lineList.append(line2)
    
    angleTuple = rs.Angle2(line1, line2)
    angle = angleTuple[0]
    
    param = rs.CurveClosestPoint(curve, midPoint)
    (curve1, curve2) = rs.SplitCurve(curve, param)
    curveList.append(curve1)
    curveList.append(curve2)
    if rs.CurveLength(curve1) > width*2:
        curveDeviation = rs.CurveDeviation(curve1, line1)
        if curveDeviation:
            if curveDeviation[2] > deviationMax:
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

def curveoverlap():
    (curve2, line2) = rs.SelectedObjects()
    print rs.CurveDeviation(curve2, line2)

#curveoverlap()

def Segmenter(angleMax, deviationMax, width, curve):
    lineList = []
    curveList = []
    
    (lineList, curveList, numberOfSegments) = firstSegmenter(curve, lineList, curveList, angleMax,deviationMax, width)
    
    rs.JoinCurves(curveList, True)
    result = rs.JoinCurves(lineList, True)
    return result