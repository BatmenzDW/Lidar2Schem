from bs4 import BeautifulSoup
import os
import re
import subprocess

from Util import *

class LAZObject:

    def __init__(self, laz_link) -> None:
        self.laz_link = laz_link
        self.laz_zip = None
        self.meta_xml = None
        self.laz_txt = None
        self.proj_name = None
        self.datum_unit = None

    def download(self):
        self.laz_zip = download(self.laz_link, 'data\\')
        self.laz_proj = f'{self.laz_zip[:-4]}_projected.laz'
        self.laz_txt = f'{self.laz_zip[:-3]}txt'

    def clear_cache(self):
        for file in [self.laz_zip, self.laz_proj, self.laz_txt]:
            if os.path.exists(file):
                os.remove(file)

    # def unzip(self):
    #     las_cmd = f'laszip -i ".\\{self.laz_zip}" -otxt -oparse xyz'
    #     os.system(las_cmd)

    # def parse_meta(self):
    #     with open(self.meta_xml, 'r') as m:
    #         data = m.read()
        
    #     Bs_data = BeautifulSoup(data, 'xml')

    #     try:
    #         self.datum_unit = Bs_data.find('altunits').get_text()
    #     except:
    #         self.datum_unit = 'US survey foot'
    #     self.proj_name = Bs_data.find('mapprojn').get_text()

    #     # if self.proj_name in ["N/A", 'Transverse Mercator'] or re.search('(?i)Conus Albers', self.proj_name):
    #     if self.proj_name in ["N/A", 'Transverse Mercator']:
    #         raise Exception(f"{self.proj_name} is not a supported map projection")

    #     print(f'unit: {self.datum_unit}')
    #     print(f'projection name: {self.proj_name}')

    def project(self):
        # 'las2las -target_longlat -otxt -sp83 IN_E -survey_feet -vertical_navd88'

        # spac_datum = None
        # spac_ref = None
        # spac_unit = None
        # if re.search("(?i)NAD83", self.proj_name):
        #     spac_datum = "-sp83"
        #     print("Found datum: NAD83")
        # else:
        #     raise Exception(f"unknown reference datum: {self.proj_name}")
        
        # sub_zone, sub_code = '', ''
        # if re.search("(?i)East", self.proj_name):
        #     sub_code, sub_zone = '_E', 'East'
        # elif re.search("(?i)West", self.proj_name):
        #     sub_code, sub_zone = '_W', 'West'
        # elif re.search("(?i)North", self.proj_name):
        #     sub_code, sub_zone = '_N', 'North'
        # elif re.search("(?i)South", self.proj_name):
        #     sub_code, sub_zone = '_S', 'South'
        # elif re.search("(?i)Central", self.proj_name):
        #     sub_code, sub_zone = '_C', 'Central'
        # # elif re.search("(?i)Kentucky Single Zone", self.proj_name):
        # #     sub_code, sub_zone = '_N', ''

        # if re.search("(?i)Indiana", self.proj_name):
        #     spac_ref = f"IN{sub_code}"
        #     print(f"Found ref: {sub_zone} Indiana")
        # elif re.search("(?i)Ohio", self.proj_name):
        #     spac_ref = f"OH{sub_code}"
        #     print(f"Found ref: {sub_zone} Ohio")
        # elif re.search("(?i)Michigan", self.proj_name):
        #     spac_ref = f"MI{sub_code}"
        #     print(f"Found ref: {sub_zone} Michigan")
        # # elif re.search("(?i)Kentucky", self.proj_name):
        # #     spac_ref = f"KY{sub_code}"
        # #     print(f"Found ref: {sub_zone} Kentucky")
        # elif re.search("(?i)Illinois", self.proj_name):
        #     spac_ref = f"IL{sub_code}"
        #     print(f"Found ref: {sub_zone} Illinois")
        # else:
        #     raise Exception(f"unknown reference datum: {self.proj_name}")

        # if re.search("(?i)Survey", self.datum_unit):
        #     spac_unit = "-survey_feet"
        #     print("Found unit: Survey Feet")
        # elif re.search("(?i)Foot", self.datum_unit) or re.search("(?i)Feet", self.datum_unit):
        #     spac_unit = "-feet"
        #     print("Found unit: Feet")

        # for verbose: v = '-v'
        v = ''

        las2las_cmd = f'las2las -i "../../{self.laz_zip}" -o "../../{self.laz_proj}" -target_longlat {v}'
        las2txt_cmd = f'las2txt -i "../../{self.laz_proj}" -o "../../{self.laz_txt}" -parse xyz {v}'

        p = subprocess.Popen(f'cd ./LAStools/bin & {las2las_cmd} & {las2txt_cmd}', shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        
        line = ''
        for line in p.stdout.readlines():
            line = line.decode()
            if line != '':
                print(line)
                raise Exception(line)

    def read_latlong(self)->list:
        data = None
        with open(self.laz_txt, 'r') as file:
            data = file.read()

        data = data.split('\n')
        print(f'raw size: {len(data)}')

        data_int = [([float(da) for da in dat.split(' ') if da]) for dat in data if dat]

        return data_int
        