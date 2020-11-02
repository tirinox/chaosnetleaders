import asyncio
import json
import logging
import random

import aiohttp

FALLBACK_THORCHAIN_IP = '3.131.115.233'
THORCHAIN_SEED_URL = 'https://chaosnet-seed.thorchain.info/'  # all addresses
THORCHAIN_BASE_URL = lambda ip: f'http://{ip if ip else FALLBACK_THORCHAIN_IP}:1317'


async def get_thorchain_nodes(session):
    async with session.get(THORCHAIN_SEED_URL) as resp:
        return await resp.json()


async def get_thorchain_node_random(session):
    resp = await get_thorchain_nodes(session)
    return random.choice(resp) if resp else FALLBACK_THORCHAIN_IP


class PoolPriceCache:
    BUSD = 'BNB.BUSD-BD1'

    CACHE_FILE = '../../data/pool_info_cache.json'

    def __init__(self, session=None):
        self.logger = logging.getLogger('PoolPriceCache')
        self.nodes_ip = []
        self.pool_cache = {}
        self.file_name = self.CACHE_FILE
        self.session = session or aiohttp.ClientSession()
        try:
            self.load()
        except FileNotFoundError:
            pass
        self.counter = 0

    async def load_nodes_ip(self):
        self.nodes_ip = await get_thorchain_nodes(self.session)
        self.logger.info(f'nodes: {self.nodes_ip}')
        assert len(self.nodes_ip) > 1

    async def try_to_save(self, forced=False):
        self.counter += 1
        if self.counter >= 100 or forced:
            await asyncio.get_event_loop().run_in_executor(None, self.save)
            self.counter = 0

    def save(self):
        with open(self.file_name, 'w') as f:
            json.dump(self.pool_cache, f, indent=4)

    def load(self):
        with open(self.file_name, 'r') as f:
            self.pool_cache = json.load(f)
            print(f'loaded pool_cache ({len(self.pool_cache)} items)')

    async def get_pool_data(self, asset, height):
        if not self.nodes_ip:
            await self.load_nodes_ip()

        ip_addr = random.choice(self.nodes_ip)
        base_url = THORCHAIN_BASE_URL(ip_addr)
        url = f"{base_url}/thorchain/pool/{asset}?height={height}"
        async with self.session.get(url) as resp:
            return await resp.json()

    async def get_pool(self, asset, block_height):
        key = f"{asset}-{block_height}"
        if key in self.pool_cache:
            return self.pool_cache[key]

        pool_data = await self.get_pool_data(asset, block_height)
        if pool_data:
            clean_pool_data = {
                'balance_asset': float(pool_data['balance_asset']),
                'balance_rune': float(pool_data['balance_rune'])
            }
            self.pool_cache[key] = clean_pool_data
            return clean_pool_data

    async def get_historical_price(self, asset, height):
        asset_pool = await self.get_pool(asset, height)
        busd_pool = await self.get_pool(self.BUSD, height)

        await self.try_to_save()

        rune_price = float(busd_pool['balance_rune']) / float(busd_pool['balance_asset'])
        asset_price_in_rune = float(asset_pool['balance_rune']) / float(asset_pool['balance_asset'])
        asset_price_in_usd = asset_price_in_rune / rune_price

        return rune_price, asset_price_in_usd
