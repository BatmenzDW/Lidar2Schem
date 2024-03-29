import math
from MathUtils import MathUtils

def checkInRange(x, y, maxX, maxY):
    if (abs(x) > maxX or abs(y) > maxY):
        raise Exception("OutOfProjectionBoundsException")

def checkLongitudeLatitudeInRange(longitude, latitude):
    checkInRange(longitude, latitude, 180, 90)

class DymaxionProjection:

    def __init__(self) -> None:
        pass

    def yRot(spherical: list, rot):
        c = MathUtils.spherical2Cartesian(spherical)

        x = c[0]
        c[0] = c[2] * math.sin(rot) + x * math.cos(rot)
        c[2] = c[2] * math.cos(rot) - x * math.sin(rot)

        mag = math.sqrt(c[0] * c[0] + c[1] * c[1] + c[2] * c[2])
        c[0] /= mag
        c[1] /= mag
        c[2] /= mag

        return [ math.atan2(c[1], c[0]), math.atan2(math.sqrt(c[0] * c[0] + c[1] * c[1]), c[2]) ]

    ARC = 2 * math.asin(math.sqrt(5 - math.sqrt(5)) / math.sqrt(10))
    Z = math.sqrt(5 + 2 * math.sqrt(5)) / math.sqrt(15)
    EL = math.sqrt(8) / math.sqrt(5 + math.sqrt(5))
    EL6 = EL / 6
    DVE = math.sqrt(3 + math.sqrt(5)) / math.sqrt(5 + math.sqrt(5))
    R = -3 * EL6 / DVE
    # Number of iterations for Newton's method
    NEWTON = 5
    """
        This contains the vertices of the icosahedron,
        identified by their geographic longitude and latitude in degrees.
        When the class is loaded, a static block below converts all these coordinates
        to the equivalent spherical coordinates (longitude and colatitude), in radians.
    
        @see <a href="https://en.wikipedia.org/wiki/Regular_icosahedron#Spherical_coordinates">Wikipedia</a>
    """
    VERTICES = [
        [ 10.536199, 64.700000 ],
        [ -5.245390, 2.300882 ],
        [ 58.157706, 10.447378 ],
        [ 122.300000, 39.100000 ],
        [ -143.478490, 50.103201 ],
        [ -67.132330, 23.717925 ],
        [ 36.521510, -50.103200 ],
        [ 112.867673, -23.717930 ],
        [ 174.754610, -2.300882 ],
        [ -121.842290, -10.447350 ],
        [ -57.700000, -39.100000 ],
        [ -169.463800, -64.700000 ]
    ]

    ISO = [
            [ 2, 1, 6 ],
            [ 1, 0, 2 ],
            [ 0, 1, 5 ],
            [ 1, 5, 10 ],
            [ 1, 6, 10 ],
            [ 7, 2, 6 ],
            [ 2, 3, 7 ],
            [ 3, 0, 2 ],
            [ 0, 3, 4 ],
            [ 4, 0, 5 ], #9, qubec
            [ 5, 4, 9 ],
            [ 9, 5, 10 ],
            [ 10, 9, 11 ],
            [ 11, 6, 10 ],
            [ 6, 7, 11 ],
            [ 8, 3, 7 ],
            [ 8, 3, 4 ],
            [ 8, 4, 9 ],
            [ 9, 8, 11 ],
            [ 7, 8, 11 ],
            [ 11, 6, 7 ], #child of 14
            [ 3, 7, 8 ] #child of 15
    ]

    CENTER_MAP = [
            [ -3, 7 ],
            [ -2, 5 ],
            [ -1, 7 ],
            [ 2, 5 ],
            [ 4, 5 ],
            [ -4, 1 ],
            [ -3, -1 ],
            [ -2, 1 ],
            [ -1, -1 ],
            [ 0, 1 ],
            [ 1, -1 ],
            [ 2, 1 ],
            [ 3, -1 ],
            [ 4, 1 ],
            [ 5, -1 ], #14, left side, right to be cut
            [ -3, -5 ],
            [ -1, -5 ],
            [ 1, -5 ],
            [ 2, -7 ],
            [ -4, -7 ],
            [ -5, -5 ], #20, pseudo triangle, child of 14
            [ -2, -7 ] #21 , pseudo triangle, child of 15
    ]

    '''
        Indicates for each face if it needs to be flipped after projecting
    '''
    FLIP_TRIANGLE = [
            True, False, True, False, False,
            True, False, True, False, True, False, True, False, True, False,
            True, True, True, False, False,
            True, False
    ]

    '''
        This contains the Cartesian coordinates the centroid
        of each face of the icosahedron.
    '''
    CENTROIDS = [[0.0 for j in range(3)] for k in range(22)]

    '''
        Rotation matrices to move the triangles to the reference coordinates from the original positions.
        Indexed by the face's indices.
    '''
    ROTATION_MATRICES = [[[0.0 for i in range(3)] for j in range(3)] for k in range(22)]
    INVERSE_ROTATION_MATRICES = [[[0.0 for i in range(3)] for j in range(3)] for k in range(22)]

    FACE_ON_GRID = [
            -1, -1, 0, 1, 2, -1, -1, 3, -1, 4, -1,
            -1, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14,
            20, 19, 15, 21, 16, -1, 17, 18, -1, -1, -1,
    ]

    for i in range(1, 22):
        CENTER_MAP[i][0] *= 0.5 * ARC
        CENTER_MAP[i][1] *= ARC * MathUtils.ROOT3 / 12
        
        # Will contain the list of vertices in Cartesian coordinates
    verticesCartesian = [[None for i in range(3)] for j in range(len(VERTICES))]

        # Convert the geographic vertices to spherical in radians
    for i in range(len(VERTICES)):
        vertexSpherical = MathUtils.geo2Spherical(VERTICES[i])
        vertex = MathUtils.spherical2Cartesian(vertexSpherical)
        verticesCartesian[i] = vertex
        VERTICES[i] = vertexSpherical

    for i in range(22):

        # Vertices of the current face
        vec1 = verticesCartesian[ISO[i][0]]
        vec2 = verticesCartesian[ISO[i][1]]
        vec3 = verticesCartesian[ISO[i][2]]
            
        # Find the centroid's projection onto the sphere
        xsum = vec1[0] + vec2[0] + vec3[0]
        ysum = vec1[1] + vec2[1] + vec3[1]
        zsum = vec1[2] + vec2[2] + vec3[2]
        mag = math.sqrt(xsum * xsum + ysum * ysum + zsum * zsum)
        CENTROIDS[i] = [ xsum / mag, ysum / mag, zsum / mag ]

        centroidSpherical = MathUtils.cartesian2Spherical(CENTROIDS[i])
        centroidLambda = centroidSpherical[0]
        centroidPhi = centroidSpherical[1]

        vertex = VERTICES[ISO[i][0]]
        v = [ vertex[0] - centroidLambda, vertex[1] ]
        v = yRot(v, -centroidPhi)

        ROTATION_MATRICES[i] = MathUtils.produceZYZRotationMatrix(-centroidLambda, -centroidPhi, (math.pi / 2) - v[0])
        INVERSE_ROTATION_MATRICES[i] = MathUtils.produceZYZRotationMatrix(v[0] - (math.pi / 2), centroidPhi, centroidLambda)

    def findTriangle(self, vector: list)->int:
        min = float("inf")
        face = 0
        
        for i in range(20):
            xd = DymaxionProjection.CENTROIDS[i][0] - vector[0]
            yd = DymaxionProjection.CENTROIDS[i][1] - vector[1]
            zd = DymaxionProjection.CENTROIDS[i][2] - vector[2]

            dissq = xd * xd + yd * yd + zd * zd

            if (dissq < min):
                if (dissq < 0.1):
                    return i
                
                face = i
                min = dissq

        return face

    def triangleTransform(self, vec):
        s = DymaxionProjection.Z / vec[2]

        xp = s * vec[0]
        yp = s * vec[1]
    
        a = math.atan((2 * yp / MathUtils.ROOT3 - DymaxionProjection.EL6) / DymaxionProjection.DVE)
        b = math.atan((xp - yp / MathUtils.ROOT3 - DymaxionProjection.EL6) / DymaxionProjection.DVE)
        c = math.atan((-xp - yp / MathUtils.ROOT3 - DymaxionProjection.EL6) / DymaxionProjection.DVE)

        return [0.5 * (b - c), (2 * a - b - c) / (2 * MathUtils.ROOT3)]

    def fromGeo(self, longitude, latitude):
        checkLongitudeLatitudeInRange(longitude, latitude)

        vector = MathUtils.spherical2Cartesian(MathUtils.geo2Spherical([ longitude, latitude ]))

        face = self.findTriangle(vector)

        # apply rotation matrix (move triangle onto template triangle)
        pvec = MathUtils.matVecProdD(self.ROTATION_MATRICES[face], vector)

        projectedVec = self.triangleTransform(pvec)

        # flip triangle to correct orientation
        if (self.FLIP_TRIANGLE[face]):
            projectedVec[0] = -projectedVec[0]
            projectedVec[1] = -projectedVec[1]

        vector[0] = projectedVec[0]

        # deal with special snowflakes (child faces 20, 21)
        if (((face == 15 and (vector[0] > projectedVec[1] * MathUtils.ROOT3)) or face == 14) and vector[0] > 0):
            projectedVec[0] = 0.5 * vector[0] - 0.5 * MathUtils.ROOT3 * projectedVec[1]
            projectedVec[1] = 0.5 * MathUtils.ROOT3 * vector[0] + 0.5 * projectedVec[1]
            face += 6 #shift 14->20 & 15->21
            print(f"snowflake: {face}")

        projectedVec[0] += self.CENTER_MAP[face][0]
        projectedVec[1] += self.CENTER_MAP[face][1]

        return projectedVec