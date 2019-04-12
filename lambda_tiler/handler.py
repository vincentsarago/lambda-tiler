"""app.main: handle request for lambda-tiler."""

from typing import Tuple, Union

import re
import json

import numpy

from rio_tiler import main

from rio_tiler.profiles import img_profiles
from rio_tiler.utils import (
    array_to_image,
    get_colormap,
    expression,
    linear_rescale
)

from rio_color.operations import parse_operations
from rio_color.utils import scale_dtype, to_math_type

from lambda_proxy.proxy import API

from lambda_tiler.viewer import viewer_template

APP = API(app_name="cogeo-tiler")


def _postprocess(
    tile: numpy.ndarray,
    mask: numpy.ndarray,
    tilesize: int,
    rescale: str = None,
    color_formula: str = None,
) -> Tuple[numpy.ndarray, numpy.ndarray]:

    if tile is None:
        # Return empty tile
        tile = numpy.zeros((1, tilesize, tilesize), dtype=numpy.uint8)
        mask = numpy.zeros((tilesize, tilesize), dtype=numpy.uint8)
    else:
        if rescale:
            rescale_arr = (
                tuple(map(float, rescale.split(","))),) * tile.shape[0]
            for bdx in range(tile.shape[0]):
                tile[bdx] = numpy.where(
                    mask,
                    linear_rescale(
                        tile[bdx],
                        in_range=rescale_arr[bdx],
                        out_range=[0, 255]
                    ),
                    0,
                )
            tile = tile.astype(numpy.uint8)

        if color_formula:
            # make sure one last time we don't have
            # negative value before applying color formula
            tile[tile < 0] = 0
            for ops in parse_operations(color_formula):
                tile = scale_dtype(ops(to_math_type(tile)), numpy.uint8)

    return tile, mask


class TilerError(Exception):
    """Base exception class."""


@APP.route(
    "/viewer",
    methods=["GET"],
    cors=True,
    payload_compression_method="gzip",
    binary_b64encode=True,
)
@APP.pass_event
def viewer(
    event: object,
    url: str
) -> Tuple[str, str, str]:
    """Handle Viewer requests."""
    endpoint = "https://{domain}/{stage}".format(
        domain=event['requestContext']['domainName'],
        stage=event['requestContext']['stage']
    )
    html = viewer_template.format(
        endpoint=endpoint,
        cogurl=url
    )
    return ("OK", "text/html", html)


@APP.route(
    "/example",
    methods=["GET"],
    cors=True,
    payload_compression_method="gzip",
    binary_b64encode=True,
)
@APP.pass_event
def example(
    event: object
) -> Tuple[str, str, str]:
    """Handle Example requests."""
    url = 'https://oin-hotosm.s3.amazonaws.com/' \
          '5ac626e091b5310010e0d482/0/5ac626e091b5310010e0d483.tif'
    endpoint = "https://{domain}/{stage}".format(
        domain=event['requestContext']['domainName'],
        stage=event['requestContext']['stage']
    )
    html = viewer_template.format(
        endpoint=endpoint,
        cogurl=url
    )
    return ("OK", "text/html", html)


@APP.route(
    "/bounds",
    methods=["GET"],
    cors=True,
    payload_compression_method="gzip",
    binary_b64encode=True,
)
def bounds(url: str) -> Tuple[str, str, str]:
    """Handle bounds requests."""
    info = main.bounds(url)
    return ("OK", "application/json", json.dumps(info))


@APP.route(
    "/metadata",
    methods=["GET"],
    cors=True,
    payload_compression_method="gzip",
    binary_b64encode=True,
)
def metadata(
    url: str, pmin: Union[str, float] = 2., pmax: Union[str, float] = 98.
) -> Tuple[str, str, str]:
    """Handle bounds requests."""
    pmin = float(pmin) if isinstance(pmin, str) else pmin
    pmax = float(pmax) if isinstance(pmax, str) else pmax
    info = main.metadata(url, pmin=pmin, pmax=pmax)
    return ("OK", "application/json", json.dumps(info))


@APP.route(
    "/tiles/<int:z>/<int:x>/<int:y>.<ext>",
    methods=["GET"],
    cors=True,
    payload_compression_method="gzip",
    binary_b64encode=True,
)
@APP.route(
    "/tiles/<int:z>/<int:x>/<int:y>@<int:scale>x.<ext>",
    methods=["GET"],
    cors=True,
    payload_compression_method="gzip",
    binary_b64encode=True,
)
def tile(
    z: int,
    x: int,
    y: int,
    scale: int = 1,
    ext: str = "png",
    url: str = None,
    indexes: Union[str, Tuple[int]] = None,
    expr: str = None,
    nodata: Union[str, int, float] = None,
    rescale: str = None,
    color_formula: str = None,
    color_map: str = None,
):
    """Handle tile requests."""
    if ext == "jpg":
        driver = "jpeg"
    elif ext == "jp2":
        driver = "JP2OpenJPEG"
    else:
        driver = ext

    if indexes and expr:
        raise TilerError("Cannot pass indexes and expression")
    if not url:
        raise TilerError("Missing 'url' parameter")

    if isinstance(indexes, str):
        indexes = tuple(int(s) for s in re.findall(r"\d+", indexes))

    tilesize = scale * 256

    if nodata is not None:
        nodata = numpy.nan if nodata == "nan" else float(nodata)

    if expr is not None:
        tile, mask = expression(url, x, y, z, expr=expr, tilesize=tilesize)
    else:
        tile, mask = main.tile(
            url, x, y, z, indexes=indexes, tilesize=tilesize)

    rtile, rmask = _postprocess(
        tile, mask, tilesize, rescale=rescale, color_formula=color_formula
    )

    if color_map:
        color_map = get_colormap(color_map, format="gdal")

    options = img_profiles.get(driver, {})
    return (
        "OK",
        f"image/{ext}",
        array_to_image(rtile, rmask, img_format=driver,
                       color_map=color_map, **options),
    )


@APP.route("/favicon.ico", methods=["GET"], cors=True)
def favicon() -> Tuple[str, str, str]:
    """Favicon."""
    return ("NOK", "text/plain", "")
