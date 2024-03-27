from bs4 import BeautifulSoup
import os
import re

from Util import *

class LAZObject:

    def __init__(self, laz_link, meta_link) -> None:
        self.laz_link = laz_link
        self.meta_link = meta_link
        self.laz_zip = None
        self.meta_xml = None
        self.laz_txt = None
        self.proj_name = None
        self.datum_unit = None

    def download(self):
        self.laz_zip = download(self.laz_link, 'data\\')
        self.laz_proj = f'{self.laz_zip[:-4]}_projected.laz'
        self.laz_txt = f'{self.laz_zip[:-3]}txt'
        self.meta_xml = download(self.meta_link, 'data\\')

    # def unzip(self):
    #     las_cmd = f'laszip -i ".\\{self.laz_zip}" -otxt -oparse xyz'
    #     os.system(las_cmd)

    def parse_meta(self):
        with open(self.meta_xml, 'r') as m:
            data = m.read()
        
        Bs_data = BeautifulSoup(data, 'xml')

        try:
            self.datum_unit = Bs_data.find('altunits').get_text()
        except:
            self.datum_unit = 'US survey foot'
        self.proj_name = Bs_data.find('mapprojn').get_text()

        print(f'unit: {self.datum_unit}')
        print(f'projection name: {self.proj_name}')

    def project(self):
        # 'las2las -target_longlat -otxt -sp83 IN_E -survey_feet -vertical_navd88'

        # unit: US survey foot
        # projection name: NAD83 / Indiana East (ftUS)

        # projection name: NAD83(2011) / Ohio North (ftUS)
        
        spac_datum = None
        spac_ref = None
        spac_unit = None
        if re.search("(?i)NAD83", self.proj_name):
            spac_datum = "-sp83"
            print("Found datum: NAD83")
        else:
            raise Exception(f"unknown reference datum: {self.proj_name}")
        # TODO: add checks for other datums
        
        if re.search("(?i)Indiana", self.proj_name):
            if re.search("(?i)East", self.proj_name):
                spac_ref = "IN_E"
                print("Found ref: East Indiana")
            elif re.search("(?i)West", self.proj_name):
                spac_ref = "IN_W"
                print("Found ref: West Indiana")
            else:
                raise Exception()
        elif re.search("(?i)Ohio", self.proj_name):
            if re.search("(?i)North", self.proj_name):
                spac_ref = "OH_N"
                print("Found ref: North Ohio")
            else:
                raise Exception()
        else:
            raise Exception()

        if re.search("(?i)Survey", self.datum_unit):
            spac_unit = "-survey_feet"
            print("Found unit: Survey Feet")

        # for verbose: v = '-v'
        v = ''

        las2las_cmd = f'las2las -i "../../{self.laz_zip}" -o "../../{self.laz_proj}" -target_longlat {spac_datum} {spac_ref} {spac_unit} -vertical_navd88 -elevation_feet {v}'
        las2txt_cmd = f'las2txt -i "../../{self.laz_proj}" -o "../../{self.laz_txt}" -parse xyz {v}'
        os.system(f'cd ./LAStools/bin & {las2las_cmd} & {las2txt_cmd}')

    def read_latlong(self)->list:
        data = None
        with open(self.laz_txt, 'r') as file:
            data = file.read()

        data = data.split('\n')
        print(f'raw size: {len(data)}')

        data_int = [([float(da) for da in dat.split(' ') if da]) for dat in data if dat]

        return data_int
        