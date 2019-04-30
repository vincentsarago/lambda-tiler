"""Test: lambda-tiler API."""

import os
import json

import pytest
from mock import patch

import numpy

from lambda_tiler.handler import APP

cog_path = os.path.join(os.path.dirname(__file__), "fixtures", "cog.tif")


@pytest.fixture()
def event():
    """Event fixture."""
    return {
        "path": "/",
        "httpMethod": "GET",
        "headers": {},
        "queryStringParameters": {},
    }


def test_API_favicon(event):
    """Test /favicon.ico route."""
    event["path"] = "/favicon.ico"
    event["httpMethod"] = "GET"

    resp = {
        "body": "",
        "headers": {
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "GET",
            "Access-Control-Allow-Origin": "*",
            "Content-Type": "text/plain",
        },
        "statusCode": 204,
    }
    res = APP(event, {})
    assert res == resp


def test_API_viewer(event):
    """Test /viewer route."""
    event["path"] = f"/viewer"
    event["httpMethod"] = "GET"
    res = APP(event, {})
    assert res["statusCode"] == 500
    headers = res["headers"]
    assert headers["Content-Type"] == "application/json"
    body = json.loads(res["body"])
    assert "url" in body["errorMessage"]

    event["path"] = f"/viewer"
    event["httpMethod"] = "GET"
    event["queryStringParameters"] = {"url": cog_path}
    res = APP(event, {})
    assert res["statusCode"] == 200
    headers = res["headers"]
    assert headers["Content-Type"] == "text/html"


def test_API_tilejson(event):
    """Test /tilejson.json route."""
    event["path"] = f"/tilejson.json"
    event["httpMethod"] = "GET"
    res = APP(event, {})
    assert res["statusCode"] == 500
    headers = res["headers"]
    assert headers["Content-Type"] == "application/json"
    body = json.loads(res["body"])
    assert "url" in body["errorMessage"]

    event["path"] = f"/tilejson.json"
    event["httpMethod"] = "GET"
    event["queryStringParameters"] = {"url": cog_path}
    res = APP(event, {})
    assert res["statusCode"] == 200
    headers = res["headers"]
    assert headers["Content-Type"] == "application/json"
    body = json.loads(res["body"])
    print(body)
    assert body["name"] == "cog.tif"
    assert body["tilejson"] == "2.1.0"
    assert body["tiles"]
    assert body["tiles"][0].endswith(f"{{z}}/{{x}}/{{y}}.png?url={cog_path}")
    assert len(body["bounds"]) == 4
    assert len(body["center"]) == 2
    assert body["minzoom"] == 6
    assert body["maxzoom"] == 8

    # test with tile_format
    event["path"] = f"/tilejson.json"
    event["httpMethod"] = "GET"
    event["queryStringParameters"] = {"url": cog_path, "tile_format": "jpg"}
    res = APP(event, {})
    assert res["statusCode"] == 200
    headers = res["headers"]
    assert headers["Content-Type"] == "application/json"
    body = json.loads(res["body"])
    assert body["tiles"][0].endswith(f"{{z}}/{{x}}/{{y}}.jpg?url={cog_path}")

    # test with kwargs
    event["path"] = f"/tilejson.json"
    event["httpMethod"] = "GET"
    event["queryStringParameters"] = {"url": cog_path, "rescale": "-1,1"}
    res = APP(event, {})
    assert res["statusCode"] == 200
    headers = res["headers"]
    assert headers["Content-Type"] == "application/json"
    body = json.loads(res["body"])
    assert body["tiles"][0].endswith(
        f"{{z}}/{{x}}/{{y}}.png?url={cog_path}&rescale=-1%2C1"
    )


def test_API_bounds(event):
    """Test /bounds route."""
    event["path"] = f"/bounds"
    event["httpMethod"] = "GET"
    res = APP(event, {})
    assert res["statusCode"] == 500
    headers = res["headers"]
    assert headers["Content-Type"] == "application/json"
    body = json.loads(res["body"])
    assert "url" in body["errorMessage"]

    event["path"] = f"/bounds"
    event["httpMethod"] = "GET"
    event["queryStringParameters"] = {"url": cog_path}
    res = APP(event, {})
    assert res["statusCode"] == 200
    headers = res["headers"]
    assert headers["Content-Type"] == "application/json"
    body = json.loads(res["body"])
    assert body["url"]
    assert len(body["bounds"]) == 4


def test_API_metadata(event):
    """Test /metadata route."""
    event["path"] = f"/metadata"
    event["httpMethod"] = "GET"
    res = APP(event, {})
    assert res["statusCode"] == 500
    headers = res["headers"]
    assert headers["Content-Type"] == "application/json"
    body = json.loads(res["body"])
    assert "url" in body["errorMessage"]

    event["path"] = f"/metadata"
    event["httpMethod"] = "GET"
    event["queryStringParameters"] = {"url": cog_path}
    res = APP(event, {})
    assert res["statusCode"] == 200
    headers = res["headers"]
    assert headers["Content-Type"] == "application/json"
    body = json.loads(res["body"])
    assert body["address"]
    assert len(body["bounds"]["value"]) == 4
    assert body["bounds"]["crs"] == "EPSG:4326"
    assert len(body["statistics"].keys()) == 1
    assert len(body["statistics"]["1"]["histogram"][0]) == 20
    assert body["minzoom"]
    assert body["maxzoom"]
    assert body["band_descriptions"]

    event["path"] = f"/metadata"
    event["httpMethod"] = "GET"
    event["queryStringParameters"] = {"url": cog_path, "histogram_bins": "10"}
    res = APP(event, {})
    assert res["statusCode"] == 200
    headers = res["headers"]
    assert headers["Content-Type"] == "application/json"
    body = json.loads(res["body"])
    assert len(body["statistics"]["1"]["histogram"][0]) == 10

    event["queryStringParameters"] = {
        "url": cog_path,
        "pmin": "5",
        "pmax": "95",
        "nodata": "-9999",
        "indexes": "1",
        "overview_level": "1",
        "histogram_range": "1,1000",
    }
    res = APP(event, {})
    assert res["statusCode"] == 200
    headers = res["headers"]
    assert headers["Content-Type"] == "application/json"
    body = json.loads(res["body"])
    assert len(body["statistics"].keys()) == 1


def test_API_tiles(event):
    """Test /tiles route."""
    # test missing url in queryString
    event["path"] = f"/tiles/7/62/44.jpg"
    event["httpMethod"] = "GET"
    res = APP(event, {})
    assert res["statusCode"] == 500
    headers = res["headers"]
    assert headers["Content-Type"] == "application/json"
    body = json.loads(res["body"])
    assert body["errorMessage"] == "Missing 'url' parameter"

    # test missing expr and indexes in queryString
    event["path"] = f"/tiles/7/62/44.jpg"
    event["httpMethod"] = "GET"
    event["queryStringParameters"] = {"url": cog_path, "indexes": "1", "expr": "b1/b1"}
    res = APP(event, {})
    assert res["statusCode"] == 500
    headers = res["headers"]
    assert headers["Content-Type"] == "application/json"
    body = json.loads(res["body"])
    assert body["errorMessage"] == "Cannot pass indexes and expression"

    # test valid request with linear rescaling
    event["path"] = f"/tiles/7/62/44.png"
    event["httpMethod"] = "GET"
    event["queryStringParameters"] = {"url": cog_path, "rescale": "0,10000"}
    res = APP(event, {})
    assert res["statusCode"] == 200
    headers = res["headers"]
    assert headers["Content-Type"] == "image/png"
    assert res["body"]
    assert res["isBase64Encoded"]

    # test valid request with expression
    event["path"] = f"/tiles/7/62/44.png"
    event["httpMethod"] = "GET"
    event["queryStringParameters"] = {
        "url": cog_path,
        "expr": "b1/b1",
        "rescale": "0,1",
    }
    res = APP(event, {})
    assert res["statusCode"] == 200
    headers = res["headers"]
    assert headers["Content-Type"] == "image/png"
    assert res["body"]
    assert res["isBase64Encoded"]

    # test valid jpg request with linear rescaling
    event["path"] = f"/tiles/7/62/44.jpg"
    event["httpMethod"] = "GET"
    event["queryStringParameters"] = {
        "url": cog_path,
        "rescale": "0,10000",
        "indexes": "1",
        "nodata": "-9999",
    }
    res = APP(event, {})
    assert res["statusCode"] == 200
    headers = res["headers"]
    assert headers["Content-Type"] == "image/jpg"
    assert res["body"]
    assert res["isBase64Encoded"]

    # test valid jpg request with rescaling and colormap
    event["path"] = f"/tiles/7/62/44.png"
    event["httpMethod"] = "GET"
    event["queryStringParameters"] = {
        "url": cog_path,
        "rescale": "0,10000",
        "color_map": "schwarzwald",
    }
    res = APP(event, {})
    assert res["statusCode"] == 200
    headers = res["headers"]
    assert headers["Content-Type"] == "image/png"
    assert res["body"]
    assert res["isBase64Encoded"]

    # test scale (512px tile size)
    event["path"] = f"/tiles/7/62/44@2x.png"
    event["httpMethod"] = "GET"
    event["queryStringParameters"] = {"url": cog_path, "rescale": "0,10000"}
    res = APP(event, {})
    assert res["statusCode"] == 200
    headers = res["headers"]
    assert headers["Content-Type"] == "image/png"
    assert res["body"]
    assert res["isBase64Encoded"]

    # test no ext (partial: png)
    event["path"] = f"/tiles/7/62/44"
    event["httpMethod"] = "GET"
    event["queryStringParameters"] = {"url": cog_path, "rescale": "0,10000"}
    res = APP(event, {})
    assert res["statusCode"] == 200
    headers = res["headers"]
    assert headers["Content-Type"] == "image/png"
    assert res["body"]
    assert res["isBase64Encoded"]

    # test no ext (full: jpeg)
    event["path"] = f"/tiles/8/126/87"
    event["httpMethod"] = "GET"
    event["queryStringParameters"] = {"url": cog_path, "rescale": "0,10000"}
    res = APP(event, {})
    assert res["statusCode"] == 200
    headers = res["headers"]
    assert headers["Content-Type"] == "image/jpg"
    assert res["body"]
    assert res["isBase64Encoded"]


@patch("lambda_tiler.handler.cogTiler.tile")
def test_API_tilesMock(tiler, event):
    """Tests if route pass the right variables."""
    tilesize = 256
    tile = numpy.random.rand(3, tilesize, tilesize).astype(numpy.int16)
    mask = numpy.full((tilesize, tilesize), 255)
    mask[0:100, 0:100] = 0

    tiler.return_value = (tile, mask)

    # test no ext
    event["path"] = f"/tiles/7/62/44"
    event["httpMethod"] = "GET"
    event["queryStringParameters"] = {"url": cog_path, "rescale": "0,10000"}
    res = APP(event, {})
    assert res["statusCode"] == 200
    assert res["body"]
    assert res["isBase64Encoded"]
    headers = res["headers"]
    assert headers["Content-Type"] == "image/png"
    kwargs = tiler.call_args[1]
    assert kwargs["tilesize"] == 256
    vars = tiler.call_args[0]
    assert vars[1] == 62
    assert vars[2] == 44
    assert vars[3] == 7

    # test ext
    event["path"] = f"/tiles/7/62/44.jpg"
    event["httpMethod"] = "GET"
    event["queryStringParameters"] = {"url": cog_path, "rescale": "0,10000"}
    res = APP(event, {})
    assert res["statusCode"] == 200
    assert res["body"]
    assert res["isBase64Encoded"]
    headers = res["headers"]
    assert headers["Content-Type"] == "image/jpg"
    kwargs = tiler.call_args[1]
    assert kwargs["tilesize"] == 256
    vars = tiler.call_args[0]
    assert vars[1] == 62
    assert vars[2] == 44
    assert vars[3] == 7

    tilesize = 512
    tile = numpy.random.rand(3, tilesize, tilesize).astype(numpy.int16)
    mask = numpy.full((tilesize, tilesize), 255)
    tiler.return_value = (tile, mask)
    mask[0:100, 0:100] = 0

    # test scale
    event["path"] = f"/tiles/7/62/44@2x"
    event["httpMethod"] = "GET"
    event["queryStringParameters"] = {"url": cog_path, "rescale": "0,10000"}
    res = APP(event, {})
    assert res["statusCode"] == 200
    assert res["body"]
    assert res["isBase64Encoded"]
    headers = res["headers"]
    assert headers["Content-Type"] == "image/png"
    kwargs = tiler.call_args[1]
    assert kwargs["tilesize"] == 512
    vars = tiler.call_args[0]
    assert vars[1] == 62
    assert vars[2] == 44
    assert vars[3] == 7

    # test scale
    event["path"] = f"/tiles/7/62/44@2x.png"
    event["httpMethod"] = "GET"
    event["queryStringParameters"] = {"url": cog_path, "rescale": "0,10000"}
    res = APP(event, {})
    assert res["statusCode"] == 200
    assert res["body"]
    assert res["isBase64Encoded"]
    headers = res["headers"]
    assert headers["Content-Type"] == "image/png"
    kwargs = tiler.call_args[1]
    assert kwargs["tilesize"] == 512
    vars = tiler.call_args[0]
    assert vars[1] == 62
    assert vars[2] == 44
    assert vars[3] == 7
