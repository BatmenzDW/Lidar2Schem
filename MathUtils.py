import math

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
        lambdaC = math.atan2(cartesian[1], cartesian[0])
        phi = math.atan2(math.sqrt(cartesian[0] * cartesian[0] + cartesian[1] * cartesian[1]), cartesian[2])
        return [ lambdaC, phi ]
    
    def produceZYZRotationMatrix(a, b, c):
        sina = math.sin(a)
        cosa = math.cos(a)
        sinb = math.sin(b)
        cosb = math.cos(b)
        sinc = math.sin(c)
        cosc = math.cos(c)

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