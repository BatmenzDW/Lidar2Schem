from bs4 import BeautifulSoup
import os

from Util import *

class LAZObject:

    def __init__(self, laz_link, meta_link) -> None:
        self.laz_link = laz_link
        self.meta_link = meta_link
        self.laz_zip = None
        self.meta_xml = None
        self.laz_txt = None

    def download(self):
        self.laz_zip = download(self.laz_link)
        self.laz_txt = f'{self.laz_zip[:-3]}txt'
        self.meta_xml = download(self.meta_link)

    # def unzip(self):
    #     las_cmd = f'laszip -i ".\\{self.laz_zip}" -otxt -oparse xyz'
    #     os.system(las_cmd)

    def parse_meta(self):
        with open(self.meta_xml, 'r') as m:
            data = m.read()
        
        Bs_data = BeautifulSoup(data, 'xml')

        datum_unit = Bs_data.find('altunits').get_text()
        proj_name = Bs_data.find('mapprojn').get_text()

        print(f'unit: {datum_unit}')
        print(f'projection name: {proj_name}')

    def project(self):
        # 'las2las -target_longlat -otxt -sp83 IN_E -survey_feet -vertical_navd88'

        # unit: US survey foot
        # projection name: NAD83 / Indiana East (ftUS)
        pass