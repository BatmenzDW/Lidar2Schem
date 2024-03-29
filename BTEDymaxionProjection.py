import math

from MathUtils import MathUtils
from ConformalDymaxionProjection import ConformalDymaxionProjection
from DymaxionProjection import DymaxionProjection

class BTEDymaxionProjection(ConformalDymaxionProjection):
    THETA = math.radians(-150)
    SIN_THETA = math.sin(THETA)
    COS_THETA = math.cos(THETA)
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

    def __init__(self) -> None:
        super().__init__()

    def fromGeoArray(self, data:list)->list:
        data_out = []
        d = data[0]
        for p in data:
            c = self.fromGeo(p[0], p[1])
            data_out.append([int(c[0]), int(c[1]), int(p[2])])

        return data_out

    def fromGeo(self, longitude:float, latitude:float):
        c = super(BTEDymaxionProjection, self).fromGeo(longitude, latitude)

        x = c[0]
        y = c[1]

        easia = self.isEurasianPart(x, y)

        y -= (0.75 * DymaxionProjection.ARC * math.sqrt(3))

        if (easia):
            x += DymaxionProjection.ARC

            t = x
            x = BTEDymaxionProjection.COS_THETA * x - BTEDymaxionProjection.SIN_THETA * y
            y = BTEDymaxionProjection.SIN_THETA * t + BTEDymaxionProjection.COS_THETA * y
        else:
            x -= DymaxionProjection.ARC

        # scale up
        c[0] = y * 7318261.522857145
        c[1] = x * 7318261.522857145 # - - cancel out
        
        return c

    def isEurasianPart(self, x, y)->bool:
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