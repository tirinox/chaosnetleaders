import json
import os

import pytest

from jobs.tx.parser import TxParserV1, SubTx, TxParserV2
from helpers.constants import NetworkIdents, THOR_DIVIDER
from models.tx import ThorTx, ThorTxType

PATH = './backend/src/test/tx_examples'
DIV = THOR_DIVIDER


def inner_example_tx_gen(name):
    with open(os.path.join(PATH, name), 'r') as f:
        return json.load(f)


@pytest.fixture
def example_tx_gen():
    return inner_example_tx_gen


@pytest.fixture
def sub_tx1_json():
    return json.loads("""{
        "address": "bnb13ettsw2h5cwxecrze6y4ppd7rwpes08j4wldph",
        "coins": [
          {
            "amount": "98900000000",
            "asset": "BNB.WISH-2D5"
          }
        ],
        "memo": "SWAP:BNB.BNB::315571677",
        "txID": "DC19184E0284CF5C2F8D2026A50C84386141D6EAEC2AAD3C2B5B28FDB340D648"
      }""")


@pytest.fixture
def sub_tx2_json():
    return json.loads("""{
        "address": "bnb14h4sduxusywddpt7x3vmcy9wfzdy074jcw6anj",
        "coins": [
          {
            "amount": "22000000",
            "asset": "BNB.ETH-1C9"
          },
          {
            "amount": "9481098498",
            "asset": "BNB.RUNE-B1A"
          }
        ],
        "memo": "STAKE:BNB.ETH-1C9",
        "txID": "AE3B3C3F042BCCEFAF6E5FDB844C06638D4F4CEA18690C2D91F2DC25B8A4834F"
      }""")


@pytest.fixture
def sub_tx3_json():
    return json.loads("""{
        "address": "bnb124rn50ddmvy0g7u48mmpma4afm4laldzpken6q",
        "coins": [
          {
            "amount": "553133983000",
            "asset": "BNB.RUNE-B1A"
          },
          {
            "amount": "48383327",
            "asset": "BNB.BTCB-1DE"
          }
        ],
        "memo": "STAKE:BNB.BTCB-1DE",
        "txID": "48AAD89689DDE84B166D44BC371BE9F04E28289AA15FAC1F7998F5EB984EECAA"
      }""")


def test_sub_tx_parse(sub_tx1_json, sub_tx2_json, sub_tx3_json):
    sub_tx1 = SubTx.parse(sub_tx1_json)
    assert sub_tx1.address == 'bnb13ettsw2h5cwxecrze6y4ppd7rwpes08j4wldph'
    assert len(sub_tx1.coins) == 1
    assert sub_tx1.first_asset == 'BNB.WISH-2D5'
    assert sub_tx1.first_amount == 98900000000 / DIV
    assert sub_tx1.rune_coin is None
    assert sub_tx1.none_rune_coins[0].asset == 'BNB.WISH-2D5'
    assert sub_tx1.none_rune_coins[0].amount == 98900000000 / DIV

    sub_tx2 = SubTx.parse(sub_tx2_json)
    assert sub_tx2.address == 'bnb14h4sduxusywddpt7x3vmcy9wfzdy074jcw6anj'
    assert len(sub_tx2.coins) == 2
    assert sub_tx2.first_asset == 'BNB.ETH-1C9'
    assert sub_tx2.first_amount == 22000000 / DIV
    assert sub_tx2.rune_coin == sub_tx2.coins[1]
    assert sub_tx2.none_rune_coins[0] == sub_tx2.coins[0]

    sub_tx3 = SubTx.parse(sub_tx3_json)
    assert sub_tx3.address == 'bnb124rn50ddmvy0g7u48mmpma4afm4laldzpken6q'
    assert len(sub_tx3.coins) == 2
    assert sub_tx3.first_asset == 'BNB.RUNE-B1A'
    assert sub_tx3.first_amount == 553133983000 / DIV
    assert sub_tx3.rune_coin == sub_tx3.coins[0]
    assert sub_tx3.none_rune_coins[0] == sub_tx3.coins[1]
    assert sub_tx3.none_rune_coins[0].asset == 'BNB.BTCB-1DE'


def test_sub_tx_combine(sub_tx1_json, sub_tx2_json, sub_tx3_json):
    sub_tx1 = SubTx.parse(sub_tx1_json)
    sub_tx2 = SubTx.parse(sub_tx2_json)
    sub_tx3 = SubTx.parse(sub_tx3_json)

    comb_tx = SubTx.join_coins((sub_tx1, sub_tx2, sub_tx3))
    assert len(comb_tx.coins) == 4
    assert comb_tx.address == ''
    assets = set(c.asset for c in comb_tx.coins)
    assert 'BNB.RUNE-B1A' in assets
    assert 'BNB.BTCB-1DE' in assets
    assert 'BNB.ETH-1C9' in assets
    assert 'BNB.WISH-2D5' in assets

    for c in comb_tx.coins:
        if c.asset == 'BNB.RUNE-B1A':
            assert c.amount == 553133983000 / DIV + 9481098498 / DIV
        elif c.asset == 'BNB.BTCB-1DE':
            assert c.amount == 48383327 / DIV
        elif c.asset == 'BNB.WISH-2D5':
            assert c.amount == 98900000000 / DIV
        elif c.asset == 'BNB.ETH-1C9':
            assert c.amount == 22000000 / DIV
        else:
            assert False, 'unexpected'


def test_parser_v1_swap(example_tx_gen):
    example_tx_list = example_tx_gen(name='v1_swap.json')
    result = TxParserV1(network_id=NetworkIdents.CHAOSNET_BEP2CHAIN).parse_tx_response(example_tx_list)
    assert len(result.txs) == 50
    assert result.total_count == 211078

    for tx in result.txs:
        assert tx.hash
        assert tx.block_height > 0
        assert tx.date > 0
        assert tx.asset1 is not None or tx.asset2 is not None
        assert tx.type == ThorTxType.TYPE_SWAP

        assert tx.amount1 > 0
        assert tx.amount2 > 0
        assert tx.network == NetworkIdents.CHAOSNET_BEP2CHAIN

    tx0 = result.txs[0]
    assert tx0.date == 1613413527
    assert tx0.block_height == 2648585
    assert tx0.asset2 == 'BNB.BNB'
    assert tx0.amount2 == 2274318077 / DIV
    assert tx0.asset1 is None
    assert tx0.amount1 == 70000000000 / DIV
    assert tx0.slip == 0.0009
    assert tx0.fee == 1073372 / DIV


def test_parser_v1_double(example_tx_gen):
    example_tx_list = example_tx_gen(name='v1_dbl_swap.json')

    result = TxParserV1(network_id=NetworkIdents.CHAOSNET_BEP2CHAIN).parse_tx_response(example_tx_list)
    assert len(result.txs) == 50
    assert result.total_count == 135643

    for tx in result.txs:
        assert tx.hash
        assert tx.block_height > 0
        assert tx.date > 0
        assert tx.asset1 is not None
        assert tx.asset2 is not None  # double swap => both not none
        assert tx.type == ThorTxType.TYPE_SWAP

        assert tx.amount1 > 0
        assert tx.amount2 > 0
        assert tx.network == NetworkIdents.CHAOSNET_BEP2CHAIN

    tx0 = result.txs[0]

    assert tx0.date == 1613413139
    assert tx0.fee == 2042385115 / DIV
    assert tx0.slip == 0.0075
    assert tx0.block_height == 2648519
    assert tx0.user_address == 'bnb13ettsw2h5cwxecrze6y4ppd7rwpes08j4wldph'
    assert tx0.asset1 == 'BNB.BNB'
    assert tx0.amount1 == 828153725 / DIV
    assert tx0.asset2 == 'BNB.FTM-A64'
    assert tx0.amount2 == 564038247209 / DIV


def test_parser_v1_stake(example_tx_gen):
    example_tx_list = example_tx_gen(name='v1_stake.json')

    result = TxParserV1(network_id=NetworkIdents.CHAOSNET_BEP2CHAIN).parse_tx_response(example_tx_list)
    assert len(result.txs) == 42
    assert result.total_count == 21791

    for tx in result.txs:
        assert tx.hash
        assert tx.block_height > 0
        assert tx.date > 0
        assert tx.type == ThorTxType.TYPE_ADD_LIQUIDITY
        assert tx.amount1 > 0 or tx.amount2 > 0
        assert tx.asset1 is not None
        assert tx.network == NetworkIdents.CHAOSNET_BEP2CHAIN

    tx0 = result.txs[0]

    assert tx0.date == 1614233083
    assert tx0.fee == 0.0
    assert tx0.slip == 0.0
    assert tx0.liq_units == pytest.approx(5836882950 / DIV)
    assert tx0.asset1 == 'BNB.ADA-9F4'
    assert tx0.amount1 == pytest.approx(21153800000 / DIV)
    assert tx0.asset2 is None
    assert tx0.amount2 == pytest.approx(4494293221 / DIV)

    tx_asym = next(t for t in result.txs if t.date == 1614227672)

    assert tx_asym.user_address == 'bnb1zkkpuqxhkl376hpkja6en6gt9lrrxzw5k6p2rc'
    assert tx_asym.amount2 == 0.0
    assert tx_asym.asset1 == 'BNB.XRP-BF2'
    assert tx_asym.amount1 == pytest.approx(399754442559 / DIV)

    tx_asym_rune = next(t for t in result.txs if t.date == 1614215021)

    assert tx_asym_rune.user_address == 'bnb16znr4gq8a89eg40qzkvnp8vr30efxu9mntgykq'
    assert tx_asym_rune.amount1 == 0.0
    assert tx_asym_rune.asset1 == 'BNB.COTI-CBB'
    assert tx_asym_rune.asset2 is None
    assert tx_asym_rune.amount2 == pytest.approx(144046120246 / DIV)


def test_parser_v1_unstake(example_tx_gen):
    example_tx_list = example_tx_gen(name='v1_unstake.json')

    result = TxParserV1(network_id=NetworkIdents.CHAOSNET_BEP2CHAIN).parse_tx_response(example_tx_list)
    assert len(result.txs) == 24  # 18 are pending!
    assert result.total_count == 12500

    for tx in result.txs:
        assert tx.hash
        assert tx.block_height > 0
        assert tx.date > 0
        assert tx.type == ThorTxType.TYPE_WITHDRAW
        assert tx.amount1 > 0 and tx.amount2 > 0
        assert tx.asset1 is not None
        assert tx.asset2 is None
        assert tx.network == NetworkIdents.CHAOSNET_BEP2CHAIN

    tx0 = result.txs[0]

    assert tx0.asset1 == 'BNB.BTCB-1DE'
    assert tx0.amount1 == pytest.approx(46546272 / DIV)
    assert tx0.asset2 is None
    assert tx0.amount2 == pytest.approx(473485683282 / DIV)
    assert tx0.user_address == 'bnb12nnn740tn4d2n6tyr2kpzqz7qsesl8h8rpjwgs'


def test_parser_v1_add(example_tx_gen):
    example_tx_list = example_tx_gen(name='v1_add.json')

    result = TxParserV1(network_id=NetworkIdents.CHAOSNET_BEP2CHAIN).parse_tx_response(example_tx_list)

    assert len(result.txs) == 36
    assert result.total_count == 36

    for tx in result.txs:
        assert tx.hash
        assert tx.block_height > 0
        assert tx.date > 0
        assert tx.type == ThorTxType.OLD_TYPE_ADD
        assert tx.amount1 > 0 or tx.amount2 > 0
        assert tx.asset1 is not None
        assert tx.liq_units == 0 and tx.slip == 0.0 and tx.fee == 0
        assert tx.network == NetworkIdents.CHAOSNET_BEP2CHAIN

    tx0 = result.txs[0]

    assert tx0.asset1 == 'BNB.USDT-6D8'
    assert tx0.amount1 == 0.0  # rune only adds in this test
    assert tx0.asset2 is None
    assert tx0.amount2 == pytest.approx(2500000000000 / DIV)


def test_parser_v1_refund(example_tx_gen):
    example_tx_list = example_tx_gen(name='v1_refund.json')

    result = TxParserV1(network_id=NetworkIdents.CHAOSNET_BEP2CHAIN).parse_tx_response(example_tx_list)

    assert len(result.txs) == 13
    assert result.total_count == 3314

    for tx in result.txs:
        assert tx.hash
        assert tx.block_height > 0
        assert tx.date > 0
        assert tx.type == ThorTxType.TYPE_REFUND
        assert tx.network == NetworkIdents.CHAOSNET_BEP2CHAIN

    tx0 = result.txs[0]
    assert tx0.user_address == 'bnb143cx0wzff603u29hvvvnq00hmr9tx9p7n4tfdr'
    assert tx0.asset1 == '.'
    assert tx0.amount1 == 0.0
    assert tx0.amount2 == pytest.approx(527077000000 / DIV)


# -------------------- V2 -------------------


def test_parser_v2_swap(example_tx_gen):
    example_tx_list = example_tx_gen(name='v2_swap.json')
    result = TxParserV2(network_id=NetworkIdents.TESTNET_MULTICHAIN).parse_tx_response(example_tx_list)
    assert len(result.txs) == 30
    assert result.total_count == 812

    for tx in result.txs:
        assert tx.hash
        assert tx.block_height > 0
        assert tx.date > 0
        assert tx.asset1 is not None or tx.asset2 is not None
        assert tx.type == ThorTxType.TYPE_SWAP
        assert tx.amount1 > 0
        assert tx.amount2 > 0

    tx_dbl_swap = next(tx for tx in result.txs if tx.date == 1614102869)
    assert tx_dbl_swap.block_height == 272436
    assert tx_dbl_swap.user_address == 'tb1q7lazuy5h4r9d3zvruj462pcjckuu784qjdhr7k'
    assert tx_dbl_swap.asset1 == 'BTC.BTC'
    assert tx_dbl_swap.amount1 == pytest.approx(928909 / DIV)
    assert tx_dbl_swap.asset2 == 'BNB.BNB'
    assert tx_dbl_swap.amount2 == pytest.approx(58385053 / DIV)

    tx0 = result.txs[0]
    assert tx0.block_height == 285211
    assert tx0.date == 1614180238
    assert tx0.asset1 is None
    assert tx0.amount1 == pytest.approx(90000000000 / DIV)
    assert tx0.asset2 == 'BTC.BTC'
    assert tx0.amount2 == pytest.approx(1719159 / DIV)
    assert tx0.slip == pytest.approx(208 / 10000)
    assert tx0.fee == pytest.approx(1828747694 / DIV)

    tx_inv = next(tx for tx in result.txs if tx.date == 1614137740)
    assert tx_inv.block_height == 278207
    assert tx_inv.user_address == 'tb1qrenvgjmg3wzl23u3wl2dw9umcds8gv2ewff7a2'
    assert tx_inv.asset1 == 'BTC.BTC'
    assert tx_inv.amount1 == pytest.approx(488650 / DIV)
    assert tx_inv.asset2 is None
    assert tx_inv.amount2 == pytest.approx(22486553084 / DIV)


def test_parser_v2_add(example_tx_gen):
    example_tx_list = example_tx_gen(name='v2_add.json')
    result = TxParserV2(network_id=NetworkIdents.TESTNET_MULTICHAIN).parse_tx_response(example_tx_list)
    assert len(result.txs) == 29
    assert result.total_count == 262

    for tx in result.txs:
        assert tx.block_height > 0
        assert tx.date > 0
        assert tx.asset1 is not None or tx.asset2 is not None
        assert tx.type == ThorTxType.TYPE_ADD_LIQUIDITY
        assert tx.amount1 > 0 or tx.amount2 > 0
        assert tx.hash

    tx0 = result.txs[0]  # both, rune first
    assert tx0.block_height == 285155
    assert tx0.user_address == 'tthor19rxk8wqd4z3hhemp6es0zwgxpwtqvlx2a7gh68'
    assert tx0.liq_units == pytest.approx(2416906866 / DIV)
    assert tx0.asset1 is None
    assert tx0.amount1 == pytest.approx(10059187641 / DIV)
    assert tx0.asset2 == "BTC.BTC"
    assert tx0.amount2 == pytest.approx(340000 / DIV)

    tx1 = result.txs[1]  # both, rune second
    assert tx1.block_height == 278364
    assert tx1.user_address == 'tthor1dqj9w9k39659h8dkrnn05teqwnfe87l5zf38hh'
    assert tx1.liq_units == pytest.approx(748901309 / DIV)
    assert tx1.asset1 == 'ETH.USDT-0X62E273709DA575835C7F6AEF4A31140CA5B1D190'
    assert tx1.amount1 == pytest.approx(1000000000 / DIV)
    assert tx1.asset2 is None
    assert tx1.amount2 == pytest.approx(6975663560 / DIV)

    tx_rune_only = next(tx for tx in result.txs if tx.date == 1614055661)
    assert tx_rune_only.user_address == 'tthor1xzwpeenj3t8y445w0u4uplzuuh2f0d59qwh5hg'
    assert tx_rune_only.amount2 == 0.0
    assert tx_rune_only.asset2 == 'BTC.BTC'
    assert tx_rune_only.amount1 == pytest.approx(17050528423 / DIV)

    tx_bnb_only = next(tx for tx in result.txs if tx.date == 1614137483)
    assert tx_bnb_only.user_address == 'tbnb1hs33v9yfwr4559vzhhw45yvrqa6c7wpeegjpyn'
    assert tx_bnb_only.asset1 == 'BNB.BNB'
    assert tx_bnb_only.amount1 == pytest.approx(1925000 / DIV)
    assert tx_bnb_only.asset2 is None


def test_parser_v2_refund(example_tx_gen):
    example_tx_list = example_tx_gen(name='v2_refund.json')
    result = TxParserV2(network_id=NetworkIdents.TESTNET_MULTICHAIN).parse_tx_response(example_tx_list)
    assert len(result.txs) == 30
    assert result.total_count == 292

    for tx in result.txs:
        assert tx.block_height > 0
        assert tx.date > 0
        assert tx.asset1 is not None or tx.asset2 is not None
        assert tx.type == ThorTxType.TYPE_REFUND
        assert tx.amount1 > 0 or tx.amount2 > 0
        assert tx.hash

    tx0 = result.txs[0]  # both, rune first
    assert tx0.block_height == 285240
    assert tx0.user_address == 'tbnb1luw9phmu48ms083wtvrl80pd839gj84pm64cpp'
    assert tx0.liq_units == 0.0
    assert tx0.asset1 == 'BNB.BNB'
    assert tx0.amount1 == pytest.approx(10000000 / DIV)
    assert tx0.asset2 == "BNB.BNB"
    assert tx0.amount2 == pytest.approx(9887500 / DIV)
    assert tx0.hash == 'ABF39ED2E295D5115201CAB5F317A8A3FEC3E05C916D8190EABFD1060D990DC6'


def test_parser_v2_withdraw(example_tx_gen):
    example_tx_list = example_tx_gen(name='v2_withdraw.json')
    result = TxParserV2(network_id=NetworkIdents.TESTNET_MULTICHAIN).parse_tx_response(example_tx_list)
    assert len(result.txs) == 29
    assert result.total_count == 98

    for tx in result.txs:
        assert tx.block_height > 0
        assert tx.date > 0
        assert tx.asset1 is not None or tx.asset2 is not None
        assert tx.type == ThorTxType.TYPE_WITHDRAW
        assert tx.amount1 > 0 and tx.amount2 > 0
        assert tx.hash

    tx0 = result.txs[0]  # both, rune first
    assert tx0.block_height == 279695
    assert tx0.user_address == 'tthor1qkd5f9xh2g87wmjc620uf5w08ygdx4etu0u9fs'
    assert tx0.liq_units == pytest.approx(-350035000000 / DIV)
    assert tx0.asset1 == 'LTC.LTC'
    assert tx0.amount1 == pytest.approx(8827053308 / DIV)
    assert tx0.asset2 is None
    assert tx0.amount2 == pytest.approx(1976877735290 / DIV)
    assert tx0.hash == 'ACD20E38D92D7C6FC68EA7702BC606C5D3809C8D7E137317FDC734D952414972'
