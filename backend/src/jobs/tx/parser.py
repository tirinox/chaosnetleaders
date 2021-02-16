import logging
from abc import ABCMeta, abstractmethod
from typing import List, NamedTuple

from helpers.coins import is_rune
from models.tx import ThorTx

logger = logging.getLogger(__name__)


class TxParseResult(NamedTuple):
    count: int = 0
    txs: List[ThorTx] = None


class TxParserBase(metaclass=ABCMeta):
    @abstractmethod
    def parse_tx_response(self, response: dict) -> TxParseResult:
        ...


class TxParserV1(TxParserBase):
    """
    Midgard V1 + Single chain BEP Swap network
    """

    def fix_tx_type(self, tx_type):
        if tx_type == ThorTx.TYPE_UNSTAKE:
            tx_type = ThorTx.TYPE_WITHDRAW
        elif tx_type == ThorTx.TYPE_DOUBLE_SWAP:
            tx_type = ThorTx.TYPE_SWAP
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
            out_tx_list = r.get('out', [{}])

            tx_hash = in_tx.get('txID', '')
            events = r.get('events', {})
            tx_type = self.fix_tx_type(r.get('type'))

            pool1, pool2 = '', ''
            input_asset, input_amount = '', 0.0
            output_asset, output_amount = '', 0.0
            input_address, output_address = '', ''

            if tx_type in (ThorTx.TYPE_SWAP, ThorTx.TYPE_DOUBLE_SWAP):
                input_address = in_tx.get('address', '')
                in_coins = in_tx.get('coins', [{}])
                input_amount = int(in_coins.get('amount')) * mult
                input_asset = str(in_coins.get('asset', ''))

                out_tx0 = out_tx_list[0]
                output_address = out_tx0.get('address', '')
                out_coins = out_tx0.get('coins', [{}])
                output_amount = int(out_coins.get('amount')) * mult
                output_asset = str(out_tx0.get('asset'))

                if is_rune(output_asset) or is_rune(input_asset):
                    # ordinary swap
                    pool1 = output_asset if is_rune(input_asset) else input_asset
                    pool2 = None
                else:
                    # double swap
                    pool1 = input_asset
                    pool2 = output_asset
            elif tx_type in (ThorTx.TYPE_WITHDRAW, ThorTx.TYPE_UNSTAKE):
                ...
            elif tx_type in (ThorTx.TYPE_ADD, ThorTx.TYPE_DONATE):
                ...

            txs.append(ThorTx(
                id=int(r.get('id', 0)),
                block_height=int(r.get('height', 0)),
                hash=tx_hash,
                type=tx_type,
                date=int(r.get('date', 0)),
                pool1=pool1,
                pool2=pool2,
                input_address=input_address,
                input_asset=input_asset,
                input_amount=input_amount,
                output_address=output_address,
                output_asset=output_asset,
                output_amount=output_amount,
                rune_volume=0.0,
                usd_volume=0.0,
                fee=float(events.get('fee', 0)) * mult,
                slip=float(events.get('slip', 0)) * mult,
                stake_units=float(events.get('stakeUnits', 0)) * mult,
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
