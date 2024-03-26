import lzma
import struct

from MathUtils import MathUtils
from DymaxionProjection import DymaxionProjection

class ConformalDymaxionProjection(DymaxionProjection):
    VECTOR_SCALE_FACTOR = 1.0 / 1.1473979730192934
    SIDE_LENGTH = 256
    
    def __init__(self) -> None:
        super().__init__()
        self.inverse = self.getInverseCache()

    def triangleTransform(self, vec):
        ARC = DymaxionProjection.ARC

        c = super().triangleTransform(vec)
        x = c[0]
        y = c[1]

        c[0] /= ARC
        c[1] /= ARC

        c[0] += 0.5
        c[1] += MathUtils.ROOT3 / 6

        c = self.inverse.applyNewtonsMethod(x, y, c[0], c[1], 5)

        c[0] -= 0.5
        c[1] -= MathUtils.ROOT3 / 6

        c[0] *= ARC
        c[1] *= ARC

        return c

    class InvertableVectorField:

        def __init__(self, vx, vy) -> None:
            self.vx = vx
            self.vy = vy

        def getInterpolatedVector(self, x, y):
            SIDE_LENGTH = ConformalDymaxionProjection.SIDE_LENGTH
            # scale up triangle to be triangleSize across
            x *= ConformalDymaxionProjection.SIDE_LENGTH
            y *= ConformalDymaxionProjection.SIDE_LENGTH

            # convert to triangle units
            v = 2 * y / MathUtils.ROOT3
            u = x - v * 0.5

            u1 = int(u)
            v1 = int(v)

            if u1 < 0: 
                u1 = 0
            elif u1 >= ConformalDymaxionProjection.SIDE_LENGTH: 
                u1 = ConformalDymaxionProjection.SIDE_LENGTH - 1

            if v1 < 0:
                v1 = 0
            elif v1 >= ConformalDymaxionProjection.SIDE_LENGTH - u1:
                v1 = ConformalDymaxionProjection.SIDE_LENGTH - u1 - 1
            
            flip = 1

            if (y < -MathUtils.ROOT3 * (x - u1 - v1 - 1) or v1 == ConformalDymaxionProjection.SIDE_LENGTH - u1 - 1):
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

            return [ valx1 * w1 + valx2 * w2 + valx3 * w3,
                     valy1 * w1 + valy2 * w2 + valy3 * w3,
                     (valx3 - valx1) * SIDE_LENGTH,
                     SIDE_LENGTH * flip * (2 * valx2 - valx1 - valx3) / MathUtils.ROOT3,
                     (valy3 - valy1) * SIDE_LENGTH, 
                     SIDE_LENGTH * flip * (2 * valy2 - valy1 - valy3) / MathUtils.ROOT3 ]
        
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

    def getInverseCache(self)->InvertableVectorField:
        SIDE_LENGTH = ConformalDymaxionProjection.SIDE_LENGTH
        VECTOR_SCALE_FACTOR = ConformalDymaxionProjection.VECTOR_SCALE_FACTOR
        vx = [[0.0 for p in range(SIDE_LENGTH + 1 - i)] for i in range(SIDE_LENGTH + 1)]
        vy = [[0.0 for p in range(SIDE_LENGTH + 1 - i)] for i in range(SIDE_LENGTH + 1)]
        with open("conformal.lzma", "rb") as compressed:
            with lzma.LZMAFile(compressed, "rb") as buf:
                for v in range(SIDE_LENGTH + 1):
                    for u in range(SIDE_LENGTH + 1 - v):
                        vx[u][v] = struct.unpack('>d',buf.read(8))[0]  * VECTOR_SCALE_FACTOR
                        vy[u][v] = struct.unpack('>d',buf.read(8))[0] * VECTOR_SCALE_FACTOR

        return self.InvertableVectorField(vx, vy)