import math
from typing import List as TList
from nbtlib import File
from nbtlib.tag import *
import os,requests
import time
from datetime import datetime

from BTEDymaxionProjection import BTEDymaxionProjection
from LAZObject import LAZObject
from Util import *

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

def haversine_longlat(long1, lat1, long2, lat2):
    return haversine(lat1, long1, lat2, long2)

def haversine_point(p1, p2):
    return haversine_longlat(p1[0],p1[1],p2[1],p2[0])

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

    file_to_write.save(f'{name}.nbt')

def get_publish_date(item):
    try:
        date = item["publicationDate"]
    except:
        dates = item["dates"]
        for d in dates:
            if d["label"] == 'Publication Date':
                date = d['dateString']
                break

    return datetime.strptime(date, '%Y-%m-%d')

def main(data_ver:int, block, radius:float, origin:tuple):
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

    items = js['items']
    items = sorted(items, key=lambda item: get_publish_date(item), reverse=True)
    titles = [i["title"] for i in items]
    print(titles)

    Laz = None

    for item in items:
        print(f'Data title: {item["title"]}')
        weblinks = item['webLinks']

        d_link, m_link = get_links_from_json(weblinks)

        Laz = LAZObject(d_link, m_link)
        Laz.download()
        try:
            Laz.parse_meta()
            break
        except Exception as e:
            if len(items) == 1:
                print(e)
            print("Skipped because of unsupported datum reference point")
            Laz.clear_cache()
            Laz = None
            continue

    if Laz == None:
        raise Exception("No Supported Data Sources in region")

    Laz.project()
    latlong_data = Laz.read_latlong()

    latlong_data = [data for data in latlong_data if haversine_point(data, origin) <= radius]

    if not latlong_data:
        raise Exception('No data withing radius.')

    proj = BTEDymaxionProjection()

    proj_data = proj.fromGeoArray(latlong_data)

    min_x = min(proj_data, key= lambda t: t[0])[0]
    min_y = min(proj_data, key= lambda t: t[2])[2]
    min_z = min(proj_data, key= lambda t: t[1])[1]

    print(f'region origin: {min_x} {min_y} {min_z}')

    # Flip y and z data, and normalize data
    proj_data = [[data[0] - min_x, data[2] - min_y, data[1] - min_z] for data in proj_data]

    min_x = min(proj_data, key= lambda t: t[0])[0]
    min_y = min(proj_data, key= lambda t: t[1])[1]
    min_z = min(proj_data, key= lambda t: t[2])[2]

    if min_x != 0 or min_y != 0 or min_z != 0:
        raise Exception("Start not at 0")
    
    max_x = max(proj_data, key= lambda t: t[0])[0] + 1
    max_y = max(proj_data, key= lambda t: t[1])[1] + 1
    max_z = max(proj_data, key= lambda t: t[2])[2] + 1

    print(f'region size: {[max_x, max_y, max_z]}')

    write_as_nbt((Laz.laz_txt[:-4]).lower(), block, proj_data, x_size=max_x, y_size=max_y, z_size=max_z, data_ver=data_ver)

    Laz.clear_cache()

    end = time.time()

    print(f'Runtime: {end-start:0.2f} s')
    return

def get_links_from_json(weblinks):
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

    return (d_link, m_link)

if __name__ == "__main__":
    main(1343, ['white','minecraft:wool'], 100, (41.18003992132766, -85.05965948610825, 41.18003992132766, -85.05965948610825))