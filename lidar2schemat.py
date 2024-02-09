import math
from typing import List as TList
from nbtlib import File
from nbtlib.tag import *
import os,requests

def download(url:str)->str:
    get_response = requests.get(url,stream=True)
    file_name  = url.split("/")[-1]
    with open(file_name, 'wb') as f:
        for chunk in get_response.iter_content(chunk_size=1024):
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)
    return file_name

def write_as_nbt(name:str,block:str,blocks:TList[TList[int]],x_size:int,z_size:int,y_size:int):

    palette = List[Compound]([
        {
            'Name': String(block)
        }
    ])
    
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
            'DataVersion': Int(3578)
            })
    }), gzipped=True)

    file_to_write.save(f'./schematics/{name}.nbt')

if __name__ == "__main__":



    # bbox = '-85.11924233672808,41.078807366445303,-85.11924233672808,41.078807366445303'
    # dataset = 'Lidar%20Point%20Cloud%20%28LPC%29'

    # gets item list json from api
    # URL = f'https://tnmaccess.nationalmap.gov/api/v1/products?bbox={bbox}&datasets={dataset}&outputFormat=JSON'

    # rq = requests.get(url = URL)
    # js = rq.json()

    # sb_URL = js['sciencebaseQuery']

    # rq = requests.get(url= sb_URL)
    # js = rq.json()

    # #TODO: choose which item to use (not just the first)
    # item = js['items'][0]
    
    # weblinks = item['webLinks']

    # d_link = None
    # for link in weblinks:
    #     if link['type'] == 'download' and link['title'] == 'LAZ':
    #         d_link = link['uri']
    #         break

    # laz_zip = download(d_link)
    # laz_txt = f'{laz_zip[:-3]}txt'

    laz_txt = 'USGS_LPC_Eastern_Indiana_QL3_Lidar__in2012_04752120_12.txt'

    # las_cmd = f'laszip -i ".\\{laz_zip}" -otxt -oparse xyz'
    # os.system(las_cmd)

    data_file = open(laz_txt, 'r')

    data = data_file.read()

    data = data.split('\n')[::10]

    print(f'size: {len(data)}')

    survey_m = (3937/1200)

    data_int = [[int(float(da)*survey_m) for da in dat.split(' ') if da] for dat in data if dat]

    min_x = min(data_int, key= lambda t: t[0])[0]
    min_y = min(data_int, key= lambda t: t[1])[1]
    min_z = min(data_int, key= lambda t: t[2])[2]
    #TODO: find correct factors
    # Flips y and z data
    data_int = [[(dat[0]-min_x)//10, (dat[2]-min_z)//10, (dat[1]-min_y)//100] for dat in data_int]

    min_x = min(data_int, key= lambda t: t[0])[0]
    min_y = min(data_int, key= lambda t: t[1])[1]
    min_z = min(data_int, key= lambda t: t[2])[2]

    if min_x != 0 or min_y != 0 or min_z != 0:
        raise Exception("Start not at 0")

    max_x = max(data_int, key= lambda t: t[0])[0]
    max_y = max(data_int, key= lambda t: t[1])[1]
    max_z = max(data_int, key= lambda t: t[2])[2]

    print(f'x: {max_x}, y: {max_y}, z: {max_z}')

    write_as_nbt((laz_txt[:-4]).lower(), 'minecraft:white_wool', data_int, x_size=max_x, y_size=max_y, z_size=max_z)