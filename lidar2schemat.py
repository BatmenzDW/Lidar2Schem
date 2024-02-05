from typing import List as TList
from nbtlib import File
from nbtlib.tag import *

def get_blocks_nbt(blocks:TList[TList[int]])->List[Compound]:
    blocks_nbt = []
    for block in blocks:
        block_nbt = {
            'state': Int(0),
            'pos': List[Int](block)
            }
        blocks_nbt.append(block_nbt)
        
    return List[Compound](blocks_nbt)

def write_as_nbt(name:str,block:str,blocks:TList[TList[int]],x_size:int,z_size:int,y_size:int):

    palette = List[Compound]([
        {
            'Name': String(block)
        }
    ])

    block_tags = get_blocks_nbt(blocks)
    
    file_to_write = File(Compound({
        "": Compound({
            'size': List[Int]([
                x_size,
                y_size,
                z_size
            ]),
            'blocks': block_tags,
            'palette': palette,
            'entities': List([]),
            'DataVersion': Int(3578)
            })
    }), gzipped=True)

    file_to_write.save(f'./nbt/{name}.nbt')

if __name__ == "__main__":
    
    bbox = '41.07946245509641,%20-85.11562494076908,%2041.076518602808534,%20-85.11903662758007'
    dataset = 'Lidar%20Point%20Cloud%20(LPC)'

    base_url = f'https://tnmaccess.nationalmap.gov/api/v1/products?bbox={bbox}&datasets={dataset}'

    # TODO: get item list json from api


    pass
    # name = 'lidar'
    # block = 'minecraft:white_wool'
    # blocks:TList[TList[int]] = [
    #     [0, 0, 0],
    #     [0, 0, 1],
    #     [0, 1, 0],
    #     [0, 1, 1],
    #     [1, 0, 0],
    #     [1, 0, 1],
    #     [1, 1, 0],
    #     [1, 1, 1]
    # ]
    # x_size = 2
    # y_size = 2
    # z_size = 2

    # write_as_nbt(name, block, blocks, x_size, z_size, y_size)