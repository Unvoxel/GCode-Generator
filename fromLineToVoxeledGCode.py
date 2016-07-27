import rhinoscriptsyntax as rs
import Rhino
import math
from Theory import *
from GCodeRead import *
from Segmenter import *


def createVoxeledGCode(voxeledLine, firstLayerHeight):
    
    voxeledGCode = []
    points = []
    
    rs.SelectObject(voxeledLine)
    rs.Command('explode')
    explodedVoxeledLines = rs.LastCreatedObjects()
    numberOfLines = len(explodedVoxeledLines)
    points += rs.CurveStartPoint(explodedVoxeledLines[0])
    for i in range(0, numberOfLines):
        point = rs.CurveEndPoint(explodedVoxeledLines[i])
        points += point
    for j in range(0, len(points)):
        if j%3 == 0:
            newPoint = [1]
            newPoint += [points[j + 2] + firstLayerHeight]
            newPoint += [points[j + 0]]
            newPoint += [points[j + 1]]
            newPoint += [0]
            newPoint += [0]
            voxeledGCode += [newPoint]
    rs.Command('join')
    numberOfPoints = len(voxeledGCode)
    return (voxeledGCode, numberOfPoints)

#print createVoxeledGCode()

def addE(thickness, width, voxeledGCode, numberOfPoints):
    numberOfRotations = fromGeotoNr(thickness, width) #give the number of rotations of the extruder for 1m of path
    voxeledGCode[0][5] = 2
    E = fromNrtoE(numberOfRotations) #give E for 1m of path
    for i in range(1, numberOfPoints):
        pathLength = math.sqrt((voxeledGCode[i][1] - voxeledGCode[i-1][1])**2 + (voxeledGCode[i][2] - voxeledGCode[i-1][2])**2 + (voxeledGCode[i][3] - voxeledGCode[i-1][3])**2) #in mm
        voxeledGCode[i][4] = E * pathLength / 1000 + voxeledGCode[i-1][4]
    return voxeledGCode

def addF(speed, voxeledGCode, numberOfPoints):
    for i in range(0, numberOfPoints):
        voxeledGCode[i][5] = speed * 60
    return voxeledGCode

def selectCurves():
    crv = []
    while True:
        objectId = rs.GetObject("Select the paths in the right order", 4)
        if not(objectId):
            break
        crv.append(objectId)
    return crv

def fromLineToGCode(thickness, width, speed, filename, angleMax, deviationMax, firstLayerHeight):
    curves = selectCurves()
    rs.UnselectAllObjects()
    numberOfCurves = len(curves)
    unvoxeledGCode = []
    
    for i in range(0, numberOfCurves):
        voxeledLine = Segmenter(angleMax, deviationMax, width, curves[i])
        (voxeledGCode, numberOfPoints) = createVoxeledGCode(voxeledLine, firstLayerHeight)
        voxeledGCode = addE(thickness, width, voxeledGCode, numberOfPoints)
        voxeledGCode = addF(speed, voxeledGCode, numberOfPoints)
        voxeledGCode.append([92, 0, 0, 0, 3200])
        unvoxeledGCode.append(unvoxelGCode(voxeledGCode, numberOfPoints, 1))
    
    fullFilename = 'C:/Users/JB/Documents/1 - Technical/1 - Design/3 - GCode/1 - Import folder/1 - GCode from Unvoxel/test.txt'
    
    writeFile( fullFilename, unvoxeledGCode[0] )

fromLineToGCode(3, 3, 30, 'test', 3, 1, 20)