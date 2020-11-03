import asyncio
import json
import logging
import random
from dataclasses import dataclass

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


@dataclass
class PoolBalance:
    balance_asset: int
    balance_rune: int

    @classmethod
    def from_dict(cls, pool_data):
        return PoolBalance(int(pool_data['balance_asset']), int(pool_data['balance_rune']))

    @property
    def to_dict(self):
        return {
            'balance_asset': self.balance_asset,
            'balance_rune': self.balance_rune
        }


class PoolPriceFetcher:
    BUSD = 'BNB.BUSD-BD1'
    RUNE_SYMBOL = 'BNB.RUNE-B1A'

    def __init__(self, session=None):
        self.logger = logging.getLogger('PoolPriceFetcher')
        self.nodes_ip = []
        self.session = session or aiohttp.ClientSession()

    async def load_nodes_ip(self):
        self.nodes_ip = await get_thorchain_nodes(self.session)
        self.logger.info(f'nodes loaded: {self.nodes_ip}')
        assert len(self.nodes_ip) > 1

    async def fetch_pool_data(self, asset, height) -> PoolBalance:
        if asset == self.RUNE_SYMBOL:
            return PoolBalance(1, 1)

        if not self.nodes_ip:
            await self.load_nodes_ip()

        ip_addr = random.choice(self.nodes_ip)
        base_url = THORCHAIN_BASE_URL(ip_addr)
        url = f"{base_url}/thorchain/pool/{asset}?height={height}"
        async with self.session.get(url) as resp:
            j = await resp.json()
            return PoolBalance.from_dict(j)

    async def get_price_in_rune(self, asset, height):
        if asset == self.RUNE_SYMBOL:
            return 1.0
        asset_pool = await self.fetch_pool_data(asset, height)
        asset_per_rune = asset_pool.balance_asset / asset_pool.balance_rune
        return asset_per_rune

    async def get_historical_price(self, asset, height):
        dollar_per_rune = await self.get_price_in_rune(self.BUSD, height)
        asset_per_rune = await self.get_price_in_rune(asset, height)

        asset_price_in_usd = dollar_per_rune / asset_per_rune

        return dollar_per_rune, asset_price_in_usd


class PoolPriceCache:
    SAVE_THRESHOLD = 20
    CACHE_FILE = '../../data/pool_info_cache.json'

    def __init__(self):
        self.logger = logging.getLogger('PoolPriceCache')
        self.price_cache = {}
        self.counter = 0
        self.file_name = self.CACHE_FILE

    async def try_to_save(self, forced=False):
        self.counter += 1
        if self.counter >= self.SAVE_THRESHOLD or forced:
            await asyncio.get_event_loop().run_in_executor(None, self.save)
            self.counter = 0

    def save(self):
        with open(self.file_name, 'w') as f:
            json.dump(self.price_cache, f, indent=4)

    def load(self):
        try:
            with open(self.file_name, 'r') as f:
                self.price_cache = json.load(f)
                self.logger.info(f'loaded pool_cache ({len(self.price_cache)} items)')
        except FileNotFoundError:
            pass

    async def get_price_in_rune(self, fetcher, asset, height):
        if asset == PoolPriceFetcher.RUNE_SYMBOL:
            return 1.0

        key = f"{asset}:{height}"
        if key in self.price_cache:
            return self.price_cache[key]
        else:
            asset_pool = await fetcher.fetch_pool_data(asset, height)
            asset_per_rune = asset_pool.balance_asset / asset_pool.balance_rune
            self.price_cache[key] = asset_per_rune
            await self.try_to_save()
            return asset_per_rune

    async def get_historical_price(self, fetcher, asset, height):
        dollar_per_rune = await self.get_price_in_rune(fetcher, fetcher.BUSD, height)
        asset_per_rune = await self.get_price_in_rune(fetcher, asset, height)

        asset_price_in_usd = dollar_per_rune / asset_per_rune

        return dollar_per_rune, asset_price_in_usd
