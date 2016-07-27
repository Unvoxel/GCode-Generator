import rhinoscriptsyntax as rs
import Rhino

def fromSurfaceToLine(layerHeight, srf):
    BB = rs.BoundingBox(srf)
    height = float(BB[6][2] - BB[0][2])
    numberOfLayers = int(height / layerHeight) + 1
    print numberOfLayers
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

multipleSrf(100)