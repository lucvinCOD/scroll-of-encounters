import sys
from pathlib import Path
import unittest
from unittest.mock import AsyncMock, patch
import httpx
from fastapi import HTTPException
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.services.scryfall import HEADERS, search_card_by_name

class ScryfallTests(unittest.IsolatedAsyncioTestCase):
    async def search(self, response):
        with patch('app.services.scryfall.httpx.AsyncClient') as client:
            get=AsyncMock(return_value=response)
            client.return_value.__aenter__.return_value.get=get
            result=await search_card_by_name('example')
            self.assertEqual(get.call_args.kwargs['headers'],HEADERS)
            return result
    async def test_success(self):
        result=await self.search(httpx.Response(200,json={'id':'card-id','name':'Card','image_uris':{'normal':'https://example.test/card.jpg'}}))
        self.assertEqual(result['image'],'https://example.test/card.jpg')
    async def test_missing_images_and_empty_faces(self):
        for card in [{'id':'a','name':'A'},{'id':'b','name':'B','card_faces':[]}]:
            self.assertIsNone((await self.search(httpx.Response(200,json=card)))['image'])
    async def test_double_faced(self):
        result=await self.search(httpx.Response(200,json={'id':'a','name':'A // B','card_faces':[{'image_uris':{'normal':'https://example.test/front.jpg'}}]}))
        self.assertEqual(result['image'],'https://example.test/front.jpg')
    async def test_upstream_error(self):
        for upstream,expected in [(404,404),(500,503),(429,503)]:
            with self.assertRaises(HTTPException) as caught: await self.search(httpx.Response(upstream,json={}))
            self.assertEqual(caught.exception.status_code,expected)
    async def test_network_failure(self):
        with patch('app.services.scryfall.httpx.AsyncClient') as client:
            client.return_value.__aenter__.return_value.get=AsyncMock(side_effect=httpx.ConnectError('simulated'))
            with self.assertRaises(HTTPException) as caught: await search_card_by_name('example')
            self.assertEqual(caught.exception.status_code,503)
