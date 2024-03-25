import math
import math as Math
import numpy as np
from typing import List as TList
from nbtlib import File
from nbtlib.tag import *
import os,requests
import lzma
import time

import projectionConstants

# states that use international foot instead of survery foot: 
#       OR, AZ, MT, ND, MI, SC
# states with no foot type specified:
#       MO, AK, AL, HI, [All Non-state juristictions]

def checkInRange(x, y, maxX, maxY):
    if (abs(x) > maxX or abs(y) > maxY):
        raise Exception("OutOfProjectionBoundsException")

def checkLongitudeLatitudeInRange(longitude, latitude):
    checkInRange(longitude, latitude, 180, 90)

class MathUtils:
    ROOT3 = math.sqrt(3)
    TAU = 2 * math.pi

    # Converts geographic latitude and longitude coordinates to spherical coordinates on a sphere of radius 1
    def geo2Spherical(geo):
        theta = math.radians(geo[0])
        phi = math.radians(90 - geo[1])
        return [ theta, phi ]

    def spherical2Cartesian(spherical):
        sinphi = math.sin(spherical[1])
        x = sinphi * math.cos(spherical[0])
        y = sinphi * math.sin(spherical[0])
        z = math.cos(spherical[1])
        return [ x, y, z ]
    
    def cartesian2Spherical(cartesian: list):
        lambdaC = Math.atan2(cartesian[1], cartesian[0])
        phi = Math.atan2(Math.sqrt(cartesian[0] * cartesian[0] + cartesian[1] * cartesian[1]), cartesian[2])
        return [ lambdaC, phi ]
    
    def produceZYZRotationMatrix(a, b, c):
        sina = math.sin(a)
        cosa = math.cos(a)
        sinb = Math.sin(b)
        cosb = Math.cos(b)
        sinc = Math.sin(c)
        cosc = Math.cos(c)

        mat = [[0.0 for i in range(3)] for j in range(3)]
        mat[0][0] = cosa * cosb * cosc - sinc * sina
        mat[0][1] = -sina * cosb * cosc - sinc * cosa
        mat[0][2] = cosc * sinb

        mat[1][0] = sinc * cosb * cosa + cosc * sina
        mat[1][1] = cosc * cosa - sinc * cosb * sina
        mat[1][2] = sinc * sinb

        mat[2][0] = -sinb * cosa
        mat[2][1] = sinb * sina
        mat[2][2] = cosb

        return mat
    
    def matVecProdD(matrix: list, vector: list):
        result = [0.0 for i in range(len(vector))]
        for i in range(len(result)):
            for j in range(len(matrix[i])):
                result[i] += matrix[i][j] * vector[j]

        return result

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

        ROTATION_MATRICES[i] = MathUtils.produceZYZRotationMatrix(-centroidLambda, -centroidPhi, (Math.pi / 2) - v[0])
        INVERSE_ROTATION_MATRICES[i] = MathUtils.produceZYZRotationMatrix(v[0] - (Math.pi / 2), centroidPhi, centroidLambda)

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
    
        a = Math.atan((2 * yp / MathUtils.ROOT3 - DymaxionProjection.EL6) / DymaxionProjection.DVE)
        b = Math.atan((xp - yp / MathUtils.ROOT3 - DymaxionProjection.EL6) / DymaxionProjection.DVE)
        c = Math.atan((-xp - yp / MathUtils.ROOT3 - DymaxionProjection.EL6) / DymaxionProjection.DVE)

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

class ConformalDynmaxionProjection(DymaxionProjection):
    VECTOR_SCALE_FACTOR = 1.0 / 1.1473979730192934
    SIDE_LENGTH = 256

    # TODO: load inverse matrix from file

    def __init__(self) -> None:
        self.inverse = self.InvertableVectorField([])
        super().__init__()

    def triangleTransform(self, vec):
        c = super().triangleTransform(vec)
        x = c[0]
        y = c[1]

        c[0] /= DymaxionProjection.ARC
        c[1] /= DymaxionProjection.ARC

        c[0] += 0.5
        c[1] += MathUtils.ROOT3 / 6

    class InvertableVectorField:

        def __init__(self, vx, vy) -> None:
            self.vx = vx
            self.vy = vy

        def getInterpolatedVector(self, x, y):
            SIDE_LENGTH = ConformalDynmaxionProjection.SIDE_LENGTH
            # scale up triangle to be triangleSize across
            x *= ConformalDynmaxionProjection.SIDE_LENGTH
            y *= ConformalDynmaxionProjection.SIDE_LENGTH

            # convert to triangle units
            v = 2 * y / MathUtils.ROOT3
            u = x - v * 0.5

            u1 = int(u)
            v1 = int(v)

            if u1 < 0: 
                u1 = 0
            elif u1 >= ConformalDynmaxionProjection.SIDE_LENGTH: 
                u1 = ConformalDynmaxionProjection.SIDE_LENGTH - 1

            if v1 < 0:
                v1 = 0
            elif v1 >= ConformalDynmaxionProjection.SIDE_LENGTH - u1:
                v1 = ConformalDynmaxionProjection.SIDE_LENGTH - u1 - 1
            
            flip = 1

            if (y < -MathUtils.ROOT3 * (x - u1 - v1 - 1) or v1 == ConformalDynmaxionProjection.SIDE_LENGTH - u1 - 1):
                valx1 = self.vx[u1][v1]
                valy1 = self.vy[u1][v1]
                valx2 = self.vx[u1][v1 + 1]
                valy2 = self.vy[u1][v1 + 1]
                valx3 = self.vx[u1 + 1][v1]
                valy3 = self.vy[u1 + 1][v1]

                y3 = 0.5 * MathUtils.ROOT3 * v1
                x3 = (u1 + 1) + 0.5 * v1
            else:
                valx1 = self.vx[u1][v1 + 1]
                valy1 = self.vy[u1][v1 + 1]
                valx2 = self.vx[u1 + 1][v1]
                valy2 = self.vy[u1 + 1][v1]
                valx3 = self.vx[u1 + 1][v1 + 1]
                valy3 = self.vy[u1 + 1][v1 + 1]

                flip = -1
                y = -y

                y3 = -(0.5 * MathUtils.ROOT3 * (v1 + 1))
                x3 = (u1 + 1) + 0.5 * (v1 + 1)

            w1 = -(y - y3) / MathUtils.ROOT3 - (x - x3)
            w2 = 2 * (y - y3) / MathUtils.ROOT3
            w3 = 1 - w1 - w2

            return [ valx1 * w1 + valx2 * w2 + valx3 * w3, valy1 * w1 + valy2 * w2 + valy3 * w3,
                    (valx3 - valx1) * SIDE_LENGTH, SIDE_LENGTH * flip * (2 * valx2 - valx1 - valx3) / MathUtils.ROOT3,
                    (valy3 - valy1) * SIDE_LENGTH, SIDE_LENGTH * flip * (2 * valy2 - valy1 - valy3) / MathUtils.ROOT3 ]
        
        def applyNewtonsMethod(self, expectedf, expectedg, xest, yest, iter):
            for i in range(iter):
                c = self.getInterpolatedVector(xest, yest)

                f = c[0] - expectedf
                g = c[1] - expectedg
                dfdx = c[2]
                dfdy = c[3]
                dgdx = c[4]
                dgdy = c[5]

                determinant = 1 / (dfdx * dgdy - dfdy * dgdx)

                xest -= determinant * (dgdy * f - dfdy * g)
                yest -= determinant * (-dgdx * f + dfdx * g)

            return [ xest, yest ]


class BTEDymaxionProjection(ConformalDynmaxionProjection):
    THETA = math.radians(-150)
    SIN_THETA = Math.sin(THETA)
    COS_THETA = Math.cos(THETA)
    BERING_X = -0.3420420960118339 #-0.3282152608138795
    BERING_Y = -0.322211064085279 #-0.3281491467713469
    ARCTIC_Y = -0.2 #-0.3281491467713469
    ARCTIC_M = (ARCTIC_Y - MathUtils.ROOT3 * DymaxionProjection.ARC / 4) / (BERING_X - -0.5 * DymaxionProjection.ARC)
    ARCTIC_B = ARCTIC_Y - ARCTIC_M * BERING_X
    ALEUTIAN_Y = -0.5000446805492526 #-0.5127463765943157
    ALEUTIAN_XL = -0.5149231279757507 #-0.4957832938238718
    ALEUTIAN_XR = -0.45
    ALEUTIAN_M = (BERING_Y - ALEUTIAN_Y) / (BERING_X - ALEUTIAN_XR)
    ALEUTIAN_B = BERING_Y - ALEUTIAN_M * BERING_X
    # {"projection":{"scale":{"delegate":{"flip_vertical":{"delegate":{"bte_conformal_dymaxion":{}}}},"x":7318261.522857145,"y":7318261.522857145}},"useDefaultHeights":true,"useDefaultTreeCover":true,"skipChunkPopulation":["ICE"],"skipBiomeDecoration":["TREE"],"version":2}
    # SCALE = {"x":7318261.522857145,"y":7318261.522857145}
    SCALE = {"x":7318261.522857145,"y":7318261.522857145}

    def __init__(self) -> None:
        super().__init__()

    def fromGeo(self, longitude, latitude):
        c = super(BTEDymaxionProjection, self).fromGeo(longitude, latitude)

        x = c[0]
        y = c[1]

        print(f"x: {x}, y: {y}")

        # easia = BTEDymaxionProjection.isEurasianPart(x, y)

        y -= (0.75 * DymaxionProjection.ARC * math.sqrt(3))

        if (False):
            x += DymaxionProjection.ARC

            t = x
            x = BTEDymaxionProjection.COS_THETA * x - BTEDymaxionProjection.SIN_THETA * y
            y = BTEDymaxionProjection.SIN_THETA * t + BTEDymaxionProjection.COS_THETA * y
        else:
            x -= DymaxionProjection.ARC

        # print(f"x: {y}, y: {x}")

        c[0] = y * 7318261.522857145
        c[1] = x * 7318261.522857145 # - - cancel out
        
        return c

    def isEurasianPart(x, y)->bool:
        # catch vast majority of cases in not near boundary
        if (x > 0):
            return False
        if (x < -0.5 * DymaxionProjection.ARC):
            print(f"{x} < {-0.5 * DymaxionProjection.ARC}")
            return True
        
        if (y > MathUtils.ROOT3 * DymaxionProjection.ARC / 4): # above arctic ocean
            # print(f"{y} > {MathUtils.ROOT3 * DymaxionProjection.ARC / 4}: {x < 0}")
            return x < 0
        
        if (y < BTEDymaxionProjection.ALEUTIAN_Y): #below bering sea
            return y < (BTEDymaxionProjection.ALEUTIAN_Y + BTEDymaxionProjection.ALEUTIAN_XL) - x
        
        if (y > BTEDymaxionProjection.BERING_Y): #boundary across arctic ocean
            if (y < BTEDymaxionProjection.ARCTIC_Y):
                return x < BTEDymaxionProjection.BERING_X #in strait
            return y < BTEDymaxionProjection.ARCTIC_M * x + BTEDymaxionProjection.ARCTIC_B #above strait
        return y > BTEDymaxionProjection.ALEUTIAN_M * x + BTEDymaxionProjection.ALEUTIAN_B

def download(url:str)->str:
    get_response = requests.get(url,stream=True)
    file_name  = url.split("/")[-1]
    with open(file_name, 'wb') as f:
        for chunk in get_response.iter_content(chunk_size=1024):
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)
    return file_name

def haversine(lat1, lon1, lat2, lon2):
    R = 6371 * 1000
    dLat = math.radians(lat2-lat1)
    dLon = math.radians(lon2-lon1)
    a = math.sin(dLat/2) * math.sin(dLat/2) +\
        math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *\
        math.sin(dLon/2) * math.sin(dLon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    d = R * c
    return d

def get_origin_point(bbox: dict, origin: tuple):
    origin_x = haversine(bbox['minLat'], bbox['minLon'], origin[0], bbox['minLon'])
    origin_y = haversine(bbox['minLat'], bbox['minLon'], bbox['minLat'], origin[1])
    return (origin_y,origin_x)

def filter_by_distance(blocks: TList[TList[int]], origin: tuple, radius)->TList[TList[int]]:
    filtered_blocks = []

    for block in blocks:
        x_d = (block[0]-origin[0]) ** 2
        y_d = (block[2]-origin[1]) ** 2
        dist = math.sqrt(x_d + y_d)
        if dist <= radius:
            filtered_blocks.append(block)

    print(f'Blocks within a radius of {radius}: {len(filtered_blocks)}')
    return filtered_blocks

def write_as_nbt(name:str,block,blocks:TList[TList[int]],x_size:int,z_size:int,y_size:int, data_ver:int):

    palette = None
    if data_ver == 3578:
        palette = List[Compound]([
            {
                'Name': String(block)
            }
        ])
    elif data_ver == 1343:
        if type(block) != list:
            raise Exception('Expected block to be a list')
        palette = List[Compound]([
            {
                'Properties': Compound(
                {
                    'color': String(block[0])
                }),
                'Name': String(block[1])
            }
        ])
    else:
        raise Exception('unsupported data version')
    
    file_to_write = None

    if data_ver == 3578:
        file_to_write = File(Compound({
            "": Compound({
                'size': List[Int]([
                    x_size,
                    y_size,
                    z_size
                ]),
                'blocks': List([Compound({'state': Int(0), 'pos': List[Int](block)}) for block in blocks]),
                'palette': palette,
                'entities': List([]),
                'DataVersion': Int(data_ver)
                })
        }), gzipped=True)
    elif data_ver == 1343:
        file_to_write = File(Compound({
            "": Compound({
                'size': List[Int]([
                    x_size,
                    y_size,
                    z_size
                ]),
                'blocks': List([Compound({'state': Int(0), 'pos': List[Int](block)}) for block in blocks]),
                'palette': palette,
                'entities': List([]),
                'DataVersion': Int(data_ver),
                'ForgeDataVersion': Compound({
                    'minecraft': Int(data_ver)
                }),
                'author': String('lidar2schemat')
            })
        }), gzipped=True)
    else:
        raise Exception('unsupported data version')

    file_to_write.save(f'./schematics/{name}.nbt')

def main(data_ver:int, block, radius:int, origin:tuple):
    start = time.time()

    bbox = f'{origin[1]},{origin[0]},{origin[3]},{origin[2]}'
    dataset = 'Lidar%20Point%20Cloud%20%28LPC%29'

    # gets item list json from api
    URL = f'https://tnmaccess.nationalmap.gov/api/v1/products?bbox={bbox}&datasets={dataset}&outputFormat=JSON'

    rq = requests.get(url = URL)
    js = rq.json()

    sb_URL = js['sciencebaseQuery']

    rq = requests.get(url= sb_URL)
    js = rq.json()

    #TODO: choose which item to use (not just the first)
    item = js['items'][0]
    print(f'Data title: {item["title"]}')

    bbox = item['spatial']['boundingBox']
    bbox = {
        'minLat': float(bbox['minY']),
        'maxLat': float(bbox['maxY']),
        'minLon': float(bbox['minX']),
        'maxLon': float(bbox['maxX'])
    }

    origin_point = get_origin_point(bbox, origin)
    
    weblinks = item['webLinks']

    d_link = None
    for link in weblinks:
        if link['type'] == 'download' and link['title'] == 'LAZ':
            d_link = link['uri']
            break

    laz_zip = download(d_link)
    laz_txt = f'{laz_zip[:-3]}txt'

    # laz_txt = 'USGS_LPC_Eastern_Indiana_QL3_Lidar__in2012_04752120_12.txt'

    las_cmd = f'laszip -i ".\\{laz_zip}" -otxt -oparse xyz'
    os.system(las_cmd)

    data_file = open(laz_txt, 'r')

    data = data_file.read()

    data = data.split('\n')

    print(f'raw size: {len(data)}')

    survey_m = (1200/3937)

    data_int = [([int(float(da)*survey_m) for da in dat.split(' ') if da]) for dat in data if dat]

    min_x = min(data_int, key= lambda t: t[0])[0]
    min_y = min(data_int, key= lambda t: t[1])[1]
    min_z = min(data_int, key= lambda t: t[2])[2]

    print(f'min x: {min_x}, min y: {min_z}, min z: {min_y}')
    
    # Flip y and z data, and normalize data
    data_int = [[(dat[0]-min_x), (dat[2]-min_z), (dat[1]-min_y)] for dat in data_int]

    data_int = filter_by_distance(data_int, origin_point, radius)

    if not data_int:
        raise Exception('No blocks within radius')

    min_x = min(data_int, key= lambda t: t[0])[0]
    min_y = min(data_int, key= lambda t: t[1])[1]
    min_z = min(data_int, key= lambda t: t[2])[2]

    # re-normalize data
    data_int = [[(dat[0]-min_x), (dat[1]-min_y), (dat[2]-min_z)] for dat in data_int]

    min_x = min(data_int, key= lambda t: t[0])[0]
    min_y = min(data_int, key= lambda t: t[1])[1]
    min_z = min(data_int, key= lambda t: t[2])[2]

    if min_x != 0 or min_y != 0 or min_z != 0:
        raise Exception("Start not at 0")

    max_x = max(data_int, key= lambda t: t[0])[0] + 1
    max_y = max(data_int, key= lambda t: t[1])[1] + 1
    max_z = max(data_int, key= lambda t: t[2])[2] + 1

    print(f'x: {max_x}, y: {max_y}, z: {max_z}')

    write_as_nbt((laz_txt[:-4]).lower(), block, data_int, x_size=max_x, y_size=max_y, z_size=max_z, data_ver=data_ver)

    end = time.time()

    print(f'Runtime: {end-start:0.2f} s')

if __name__ == "__main__":
    # main(3578, 'minecraft:white_wool', 100, (41.07707069512237, -85.11757983000066, 41.07707069512237, -85.11757983000066))
    # main(1343, ['white','minecraft:wool'], 50, (41.07707069512237, -85.11757983000066, 41.07707069512237, -85.11757983000066))
    
    # -9481521 -5876387
    # 41.180103596175286, -85.05945366396479
    # dif: 109548.18762981237

    # -9484965 -5864078
    # 41.07703106760974 -85.11730362468673
    # dif: 110549.3594007249

    # -9484948 -5864078
    # 41.07697040994484 -85.11711050563768
    # dif: 110553.8017136039
    proj = BTEDymaxionProjection()

    location = proj.fromGeo(-85.11711050563768, 41.07697040994484)
    print(location)
    difx, dify = location[0] - -9484948, location[1] - -5864078
    dif = math.sqrt(difx * difx + dify * dify)
    print(f"dif: {dif}")