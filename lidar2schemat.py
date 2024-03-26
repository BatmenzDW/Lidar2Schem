import math
from typing import List as TList
from nbtlib import File
from nbtlib.tag import *
import os,requests
import time

from BTEDymaxionProjection import BTEDymaxionProjection
from LAZObject import LAZObject
from Util import *

# states that use international foot instead of survery foot: 
#       OR, AZ, MT, ND, MI, SC
# states with no foot type specified:
#       MO, AK, AL, HI, [All Non-state juristictions]

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

    d_link, m_link = None, None
    for link in weblinks:
        if link['type'] == 'download' and link['title'] == 'LAZ':
            d_link = link['uri']
            if m_link and d_link:
                break
            continue
        if link['type'] == 'originalMetadata' and link['title'] == 'Product Metadata':
            m_link = link['uri']
            if m_link and d_link:
                break

    Laz = LAZObject(d_link, m_link)
    Laz.download()
    Laz.parse_meta()


    return

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
    main(1343, ['white','minecraft:wool'], 50, (41.07707069512237, -85.11757983000066, 41.07707069512237, -85.11757983000066))

    # proj = BTEDymaxionProjection()

    # location = proj.fromGeo(-85.11711050563768, 41.07697040994484)
    # print(location)
    # difx, dify = location[0] - -9484948, location[1] - -5864078
    # dif = math.sqrt(difx * difx + dify * dify)
    # print(f"dif: {dif}")