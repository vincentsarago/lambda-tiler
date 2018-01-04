"""
"""

import re
import json

from rio_tiler import main
from rio_tiler.utils import array_to_img

from lambda_proxy.proxy import API


APP = API(app_name="lambda-tiler")


@APP.route('/bounds', methods=['GET'], cors=True)
def bounds():
    """
    Handle bounds requests
    """

    query_args = APP.current_request.query_params
    query_args = query_args if isinstance(query_args, dict) else {}

    address = query_args['url']
    info = main.bounds(address)
    return ('OK', 'application/json', json.dumps(info))


@APP.route('/tiles/<int:z>/<int:x>/<int:y>.<ext>', methods=['GET'], cors=True)
def tile(tile_z, tile_x, tile_y, tileformat):
    """
    Handle tile requests
    """
    query_args = APP.current_request.query_params
    query_args = query_args if isinstance(query_args, dict) else {}

    address = query_args['url']

    bands = query_args.get('rgb')
    if bands:
        bands = tuple(int(s) for s in re.findall(r'\d+', bands))

    tilesize = query_args.get('tile', 256)
    tilesize = int(tilesize) if isinstance(tilesize, str) else tilesize

    nodata = query_args.get('nodata')

    tile = main.tile(address, tile_x, tile_y, tile_z, bands, tilesize=tilesize)
    tile = array_to_img(tile, tileformat, nodata=nodata)
    if tileformat == 'jpg':
        tileformat = 'jpeg'

    return ('OK', f'image/{tileformat}', tile)


@APP.route('/favicon.ico', methods=['GET'], cors=True)
def favicon():
    """
    favicon
    """
    return('NOK', 'text/plain', '')
