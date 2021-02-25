import logging
from abc import ABCMeta, abstractmethod
from collections import namedtuple, defaultdict
from typing import List, NamedTuple

import typing

from helpers.coins import is_rune
from models.tx import ThorTx, ThorTxType

logger = logging.getLogger(__name__)


class TxParseResult(NamedTuple):
    total_count: int = 0
    txs: List[ThorTx] = None


class TxParserBase(metaclass=ABCMeta):
    @abstractmethod
    def parse_tx_response(self, response: dict) -> TxParseResult:
        ...


class Coin(typing.NamedTuple):
    amount: float = 0.0
    asset: str = ''

    @classmethod
    def parse(cls, j):
        return cls(asset=j.get('asset', ''),
                   amount=int(j.get('amount', 0.0)) / ThorTx.DIVIDER)


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
        return self.coins[0].asset

    @property
    def first_amount(self):
        return self.coins[0].amount

    @classmethod
    def join_coins(cls, tx_list: typing.Iterable):
        coin_dict = defaultdict(float)
        for tx in tx_list:
            for coin in tx.coins:
                coin_dict[coin.asset] += coin.amount
        return cls(address='', coins=[Coin(amount, asset) for asset, amount in coin_dict.items()])

    @property
    def rune_coin(self):
        return next((c for c in self.coins if is_rune(c.asset)), None)

    @property
    def none_rune_coins(self):
        return [c for c in self.coins if not is_rune(c.asset)]


class TxParserV1(TxParserBase):
    """
    Midgard V1 + Single chain BEP Swap network
    """

    @staticmethod
    def fix_tx_type(tx_type):
        if tx_type == ThorTxType.TYPE_UNSTAKE:
            return ThorTxType.TYPE_WITHDRAW
        elif tx_type == ThorTxType.TYPE_DOUBLE_SWAP:
            return ThorTxType.TYPE_SWAP
        elif tx_type == ThorTxType.TYPE_STAKE:
            return ThorTxType.TYPE_ADD_LIQUIDITY
        else:
            return tx_type

    def parse_tx_response(self, response: dict) -> TxParseResult:
        raw_txs = response.get('txs', [])
        txs = []
        mult = 1.0 / ThorTx.DIVIDER

        for r in raw_txs:
            status = r.get('status', '').lower()
            if status != 'success':
                continue

            in_tx = r.get('in', {})
            if not in_tx:
                logger.warning(f'tx {r} has not txID')
                continue
            input_tx = SubTx.parse(in_tx)
            out_tx_list = [SubTx.parse(rt) for rt in r.get('out', [])]

            tx_hash = in_tx.get('txID', '')
            tx_type = self.fix_tx_type(r.get('type'))
            pool = r.get('pool', '')

            user_address = input_tx.address

            asset1, asset2 = None, None
            amount1, amount2 = 0.0, 0.0
            usd_price1, usd_price2 = 0.0, 0.0

            if tx_type == ThorTxType.TYPE_SWAP:
                input_asset, input_amount = input_tx.first_asset, input_tx.first_amount
                output_asset, output_amount = out_tx_list[0].first_asset, out_tx_list[0].first_amount
                if is_rune(input_asset):  # ordinary swap
                    asset1, amount1 = output_asset, output_amount
                    asset2, amount2 = None, input_amount  # none = Rune
                elif is_rune(output_asset):  # ordinary swap
                    asset1, amount1 = input_asset, input_amount
                    asset2, amount2 = None, output_amount  # none = Rune
                else:  # double swap
                    asset1, amount1 = input_asset, input_amount
                    asset2, amount2 = output_asset, output_amount
            elif tx_type == ThorTxType.TYPE_WITHDRAW:
                out_compound = SubTx.join_coins(out_tx_list)
                not_rune_coin = out_compound.none_rune_coins[0]
                asset1 = pool
                amount1 = not_rune_coin.amount
                asset2 = None
                amount2 = out_compound.rune_coin.amount
            elif tx_type == ThorTxType.TYPE_ADD_LIQUIDITY:
                user_address = input_tx.address
                if input_tx.none_rune_coins:
                    amount1 = input_tx.none_rune_coins[0].amount
                asset1 = pool
                asset2 = None
                if input_tx.rune_coin:
                    amount2 = input_tx.rune_coin.amount
            elif tx_type in (ThorTxType.TYPE_ADD, ThorTxType.TYPE_DONATE):
                asset1 = pool
                if input_tx.rune_coin:
                    amount2 = input_tx.rune_coin.amount
                if input_tx.none_rune_coins:
                    amount1 = input_tx.none_rune_coins[0].amount
                asset2 = None

            events = r.get('events', {})

            txs.append(ThorTx(
                id=int(r.get('id', 0)),
                block_height=int(r.get('height', 0)),
                hash=tx_hash,
                type=tx_type,
                date=int(r.get('date', 0)),
                user_address=user_address,
                asset1=asset1,
                amount1=amount1,
                usd_price1=usd_price1,
                asset2=asset2,
                amount2=amount2,
                usd_price2=usd_price2,
                rune_volume=0.0,
                usd_volume=0.0,
                fee=float(events.get('fee', 0)) * mult,
                slip=float(events.get('slip', 0)),
                liq_units=float(events.get('stakeUnits', 0)) * mult,
            ))

        count = int(response.get('count', 0))
        return TxParseResult(count, txs)


class TxParserV2(TxParserBase):
    """
    Midgard V2 + Multi-chain network
    """

    def parse_tx_response(self, response: dict) -> TxParseResult:
        txs = response.get('actions', [])
        count = int(response.get('count', 0))

        return TxParseResult(0, [])