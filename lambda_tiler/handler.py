"""app.main: handle request for lambda-tiler."""

from typing import Dict, Tuple, Union
from typing.io import BinaryIO

import os
import re
import json
import urllib

import numpy

import rasterio
from rasterio import warp

from rio_tiler import main as cogTiler
from rio_tiler.mercator import get_zooms
from rio_tiler.profiles import img_profiles
from rio_tiler.utils import (
    array_to_image,
    get_colormap,
    expression,
    linear_rescale,
    _chunks,
)

from rio_color.operations import parse_operations
from rio_color.utils import scale_dtype, to_math_type

from lambda_proxy.proxy import API

from lambda_tiler.viewer import viewer_template

APP = API(app_name="cogeo-tiler")


def _postprocess(
    tile: numpy.ndarray,
    mask: numpy.ndarray,
    rescale: str = None,
    color_formula: str = None,
) -> Tuple[numpy.ndarray, numpy.ndarray]:
    """Post-process tile data."""
    if rescale:
        rescale_arr = list(map(float, rescale.split(",")))
        rescale_arr = list(_chunks(rescale_arr, 2))
        if len(rescale_arr) != tile.shape[0]:
            rescale_arr = ((rescale_arr[0]),) * tile.shape[0]

        for bdx in range(tile.shape[0]):
            tile[bdx] = numpy.where(
                mask,
                linear_rescale(
                    tile[bdx], in_range=rescale_arr[bdx], out_range=[0, 255]
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
def viewer_handler(event: object, url: str, **kwargs: Dict) -> Tuple[str, str, str]:
    """Handle Viewer requests."""
    host = event["headers"].get("X-Forwarded-Host", event["headers"].get("Host", ""))
    # Check for API gateway stage
    if ".execute-api." in host and ".amazonaws.com" in host:
        stage = event["requestContext"].get("stage", "")
        host = f"{host}/{stage}"

    scheme = "http://" if host.startswith("127.0.0.1") else "https://"
    endpoint = f"{scheme}{host}"

    qs = [f"{k}={v}" for k, v in kwargs.items()]
    if qs:
        qs = "&".join(qs)
    else:
        qs = ""

    html = viewer_template.format(endpoint=endpoint, cogurl=url, tile_options=qs)
    return ("OK", "text/html", html)


@APP.route(
    "/example",
    methods=["GET"],
    cors=True,
    payload_compression_method="gzip",
    binary_b64encode=True,
)
@APP.pass_event
def example_handler(event: object) -> Tuple[str, str, str]:
    """Handle Example requests."""
    url = (
        "https://oin-hotosm.s3.amazonaws.com/"
        "5ac626e091b5310010e0d482/0/5ac626e091b5310010e0d483.tif"
    )
    endpoint = "https://{domain}/{stage}".format(
        domain=event["requestContext"]["domainName"],
        stage=event["requestContext"]["stage"],
    )
    html = viewer_template.format(endpoint=endpoint, cogurl=url)
    return ("OK", "text/html", html)


@APP.route(
    "/tilejson.json",
    methods=["GET"],
    cors=True,
    payload_compression_method="gzip",
    binary_b64encode=True,
)
@APP.pass_event
def tilejson_handler(request: Dict, url: str, tile_format: str = "png", **kwargs: Dict):
    """Handle /tilejson.json requests."""
    host = request["headers"].get(
        "X-Forwarded-Host", request["headers"].get("Host", "")
    )
    # Check for API gateway stage
    if ".execute-api." in host and ".amazonaws.com" in host:
        stage = request["requestContext"].get("stage", "")
        host = f"{host}/{stage}"

    scheme = "http" if host.startswith("127.0.0.1") else "https"

    qs = urllib.parse.urlencode(list(kwargs.items()))
    tile_url = f"{scheme}://{host}/tiles/{{z}}/{{x}}/{{y}}.{tile_format}?url={url}"
    if qs:
        tile_url += f"&{qs}"

    with rasterio.open(url) as src_dst:
        bounds = warp.transform_bounds(
            *[src_dst.crs, "epsg:4326"] + list(src_dst.bounds), densify_pts=21
        )
        center = [(bounds[0] + bounds[2]) / 2, (bounds[1] + bounds[3]) / 2]
        minzoom, maxzoom = get_zooms(src_dst)

    meta = dict(
        bounds=bounds,
        center=center,
        minzoom=minzoom,
        maxzoom=maxzoom,
        name=os.path.basename(url),
        tilejson="2.1.0",
        tiles=[tile_url],
    )
    return ("OK", "application/json", json.dumps(meta))


@APP.route(
    "/bounds",
    methods=["GET"],
    cors=True,
    payload_compression_method="gzip",
    binary_b64encode=True,
)
def bounds_handler(url: str) -> Tuple[str, str, str]:
    """Handle /bounds requests."""
    info = cogTiler.bounds(url)
    return ("OK", "application/json", json.dumps(info))


@APP.route(
    "/metadata",
    methods=["GET"],
    cors=True,
    payload_compression_method="gzip",
    binary_b64encode=True,
)
def metadata_handler(
    url: str,
    pmin: Union[str, float] = 2.0,
    pmax: Union[str, float] = 98.0,
    nodata: Union[str, float, int] = None,
    indexes: Union[str, Tuple, int] = None,
    overview_level: Union[str, int] = None,
    max_size: Union[str, int] = 1024,
    histogram_bins: Union[str, int] = 20,
    histogram_range: Union[str, int] = None,
) -> Tuple[str, str, str]:
    """Handle /metadata requests."""
    pmin = float(pmin) if isinstance(pmin, str) else pmin
    pmax = float(pmax) if isinstance(pmax, str) else pmax

    if nodata is not None and isinstance(nodata, str):
        nodata = numpy.nan if nodata == "nan" else float(nodata)

    if indexes is not None and isinstance(indexes, str):
        indexes = tuple(int(s) for s in re.findall(r"\d+", indexes))

    if overview_level is not None and isinstance(overview_level, str):
        overview_level = int(overview_level)

    max_size = int(max_size) if isinstance(max_size, str) else max_size
    histogram_bins = (
        int(histogram_bins) if isinstance(histogram_bins, str) else histogram_bins
    )

    if histogram_range is not None and isinstance(histogram_range, str):
        histogram_range = tuple(map(float, histogram_range.split(",")))

    info = cogTiler.metadata(
        url,
        pmin=pmin,
        pmax=pmax,
        nodata=nodata,
        indexes=indexes,
        overview_level=overview_level,
        histogram_bins=histogram_bins,
        histogram_range=histogram_range,
    )
    return ("OK", "application/json", json.dumps(info))


@APP.route(
    "/tiles/<int:z>/<int:x>/<int:y>",
    methods=["GET"],
    cors=True,
    payload_compression_method="gzip",
    binary_b64encode=True,
)
@APP.route(
    "/tiles/<int:z>/<int:x>/<int:y>.<ext>",
    methods=["GET"],
    cors=True,
    payload_compression_method="gzip",
    binary_b64encode=True,
)
@APP.route(
    "/tiles/<int:z>/<int:x>/<int:y>@<int:scale>x",
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
def tile_handler(
    z: int,
    x: int,
    y: int,
    scale: int = 1,
    ext: str = None,
    url: str = None,
    indexes: Union[str, Tuple[int]] = None,
    expr: str = None,
    nodata: Union[str, int, float] = None,
    rescale: str = None,
    color_formula: str = None,
    color_map: str = None,
) -> Tuple[str, str, BinaryIO]:
    """Handle /tiles requests."""
    if indexes and expr:
        raise TilerError("Cannot pass indexes and expression")

    if not url:
        raise TilerError("Missing 'url' parameter")

    if isinstance(indexes, str):
        indexes = tuple(int(s) for s in re.findall(r"\d+", indexes))

    if nodata is not None:
        nodata = numpy.nan if nodata == "nan" else float(nodata)

    tilesize = scale * 256
    if expr is not None:
        tile, mask = expression(
            url, x, y, z, expr=expr, tilesize=tilesize, nodata=nodata
        )
    else:
        tile, mask = cogTiler.tile(
            url, x, y, z, indexes=indexes, tilesize=tilesize, nodata=nodata
        )

    if not ext:
        ext = "jpg" if mask.all() else "png"

    rtile, rmask = _postprocess(
        tile, mask, rescale=rescale, color_formula=color_formula
    )

    if color_map:
        color_map = get_colormap(color_map, format="gdal")

    if ext == "jpg":
        driver = "jpeg"
    elif ext == "jp2":
        driver = "JP2OpenJPEG"
    else:
        driver = ext

    options = img_profiles.get(driver, {})
    return (
        "OK",
        f"image/{ext}",
        array_to_image(rtile, rmask, img_format=driver, color_map=color_map, **options),
    )


@APP.route("/favicon.ico", methods=["GET"], cors=True)
def favicon() -> Tuple[str, str, str]:
    """Favicon."""
    return ("EMPTY", "text/plain", "")
