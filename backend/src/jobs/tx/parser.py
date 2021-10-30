import hashlib
import logging
import typing
from abc import ABCMeta, abstractmethod
from collections import defaultdict
from typing import List, NamedTuple

from helpers.coins import is_rune
from helpers.constants import NetworkIdents, THOR_DIVIDER, THOR_DIVIDER_INV
from models.tx import ThorTx, ThorTxType

logger = logging.getLogger(__name__)

dbg_hashes = set()


class TxParseResult(NamedTuple):
    total_count: int = 0
    txs: List[ThorTx] = None
    tx_count_unfiltered: int = 0
    network_id: str = ''

    @property
    def tx_count(self):
        return len(self.txs)


class TxParserBase(metaclass=ABCMeta):
    def __init__(self, network_id):
        self.network_id = network_id

    @abstractmethod
    def parse_tx_response(self, response: dict) -> TxParseResult:
        ...


class Coin(typing.NamedTuple):
    amount: float = 0.0
    asset: str = ''

    @classmethod
    def parse(cls, j):
        return cls(asset=j.get('asset', ''),
                   amount=int(j.get('amount', 0.0)) / THOR_DIVIDER)


class SubTx(typing.NamedTuple):
    address: str = ''
    coins: List[Coin] = []

    @classmethod
    def parse(cls, j):
        coins = [Coin.parse(cj) for cj in j.get('coins', [])]
        return cls(address=j.get('address', ''),
                   coins=coins)

    @property
    def first_asset(self):
        return self.coins[0].asset if self.coins else None

    @property
    def first_amount(self):
        return self.coins[0].amount if self.coins else None

    @classmethod
    def join_coins(cls, tx_list: List['SubTx']):
        coin_dict = defaultdict(float)
        address = ''
        for tx in tx_list:
            address = tx.address or address
            for coin in tx.coins:
                coin_dict[coin.asset] += coin.amount
        return cls(address, coins=[Coin(amount, asset) for asset, amount in coin_dict.items()])

    @property
    def rune_coin(self):
        return next((c for c in self.coins if is_rune(c.asset)), None)

    @property
    def none_rune_coins(self):
        return [c for c in self.coins if not is_rune(c.asset)]


class TxParserV2(TxParserBase):
    """
    Midgard V2 + Multi-chain network
    """

    def parse_tx_response(self, response: dict) -> TxParseResult:
        raw_txs = response.get('actions', [])
        count = int(response.get('count', 0))

        txs = []
        for r in raw_txs:
            status = r.get('status', '').lower()
            if status != 'success':
                continue

            tx_type = r.get('type')
            pools = r.get('pools', [])
            date = int(int(r.get('date', 0)) * 10e-10)
            metadata = r.get('metadata', {})

            in_tx_list = [SubTx.parse(rt) for rt in r.get('in', [])]
            out_tx_list = [SubTx.parse(rt) for rt in r.get('out', [])]

            user_address = in_tx_list[0].address
            fee, slip, liq_units = 0.0, 0.0, 0.0

            asset1, asset2 = None, None
            amount1, amount2 = 0.0, 0.0
            usd_price1, usd_price2 = 0.0, 0.0

            tx_hash = r.get('in', [{}])[0].get('txID', '')
            dbg_hashes.add(tx_hash)

            height = int(r.get('height', 0))

            if tx_type == ThorTxType.TYPE_SWAP:
                amount1, amount2, asset1, asset2, fee, slip = \
                    self._parse_swap(in_tx_list, metadata, out_tx_list, r, tx_type)
            elif tx_type in (ThorTxType.TYPE_ADD_LIQUIDITY, ThorTxType.TYPE_DONATE):
                asset1, amount1 = in_tx_list[0].first_asset, in_tx_list[0].first_amount
                if is_rune(asset1):
                    asset1 = None
                    asset2 = pools[0]
                    user_address = in_tx_list[0].address
                if len(in_tx_list) >= 2:
                    asset2, amount2 = in_tx_list[1].first_asset, in_tx_list[1].first_amount
                    if is_rune(asset2):
                        asset2 = None
                        asset1 = pools[0]
                        user_address = in_tx_list[1].address
                if tx_type == ThorTxType.TYPE_ADD_LIQUIDITY:
                    liq_units = int(metadata.get('addLiquidity', {}).get('liquidityUnits', 0)) * THOR_DIVIDER_INV
            elif tx_type == ThorTxType.TYPE_WITHDRAW:
                asset1 = pools[0]
                out_compound = SubTx.join_coins(out_tx_list)
                if out_compound.none_rune_coins:
                    not_rune_coin = out_compound.none_rune_coins[0]
                    amount1 = not_rune_coin.amount

                asset2 = None
                rune_out = out_compound.rune_coin
                if rune_out:
                    amount2 = rune_out.amount

                liq_units = int(metadata.get('withdraw', {}).get('liquidityUnits', 0)) * THOR_DIVIDER_INV
            elif tx_type == ThorTxType.TYPE_REFUND:
                if in_tx_list:
                    asset1 = in_tx_list[0].first_asset
                    amount1 = in_tx_list[0].first_amount
                if out_tx_list:
                    asset2 = out_tx_list[0].first_asset
                    amount2 = out_tx_list[0].first_amount
            elif tx_type == ThorTxType.TYPE_SWITCH:
                amount1 = in_tx_list[0].first_amount
                amount2 = out_tx_list[0].first_amount
                # upgrade has no tx_id?
                if not tx_hash:
                    hash_feed = f"{height}:{amount1}:{user_address}"
                    tx_hash = hashlib.sha1(hash_feed.encode()).hexdigest()
            else:
                logger.warning(f'unknown tx type: {tx_type}')
                continue

            txs.append(ThorTx(
                block_height=height,
                hash=tx_hash,
                type=tx_type,
                date=date,
                user_address=user_address,
                asset1=asset1,
                amount1=amount1,
                usd_price1=usd_price1,
                asset2=asset2,
                amount2=amount2,
                usd_price2=usd_price2,
                rune_volume=0.0,
                usd_volume=0.0,
                fee=fee,
                slip=slip,
                liq_units=liq_units,
                network=self.network_id,
            ))

        return TxParseResult(count, txs, len(raw_txs), network_id=self.network_id)

    @staticmethod
    def _parse_swap(in_tx_list, metadata, out_tx_list, r, tx_type):
        if len(in_tx_list) > 1:
            logger.warning(f'Found TX ({tx_type}) with: in_tx_list > 1! {r!r}')

        if len(out_tx_list) > 1:
            logger.warning(f'Found TX ({tx_type}) with: out_tx_list > 1! {r!r}')

        joined_in = SubTx.join_coins(in_tx_list)
        joined_out = SubTx.join_coins(out_tx_list)

        asset1, amount1 = joined_in.first_asset, joined_in.first_amount
        asset2, amount2 = joined_out.first_asset, joined_out.first_amount

        if is_rune(asset1):
            asset1 = None
        elif is_rune(asset2):
            asset2 = None
        swap_meta = metadata.get('swap', {})
        slip = int(swap_meta.get('tradeSlip', 0)) / 10000.0
        fee = int(swap_meta.get('liquidityFee', 0)) * THOR_DIVIDER_INV

        return amount1, amount2, asset1, asset2, fee, slip


def get_parser_by_network_id(network_id) -> TxParserBase:
    if network_id in (NetworkIdents.TESTNET_MULTICHAIN, NetworkIdents.CHAOSNET_MULTICHAIN):
        return TxParserV2(network_id)
    else:
        raise KeyError('unsupported network ID!')
