import json
import os

import pytest

from jobs.tx.parser import TxParserV1, SubTx
from models.tx import ThorTx, ThorTxType

PATH = './backend/src/test/tx_examples'
DIV = ThorTx.DIVIDER


@pytest.fixture
def example_tx_gen():
    def _example_tx_gen(name):
        with open(os.path.join(PATH, name), 'r') as f:
            return json.load(f)

    return _example_tx_gen


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
    result = TxParserV1().parse_tx_response(example_tx_list)
    assert len(result.txs) == 50
    assert result.total_count == 211078

    for tx in result.txs:
        assert tx.block_height > 0
        assert tx.date > 0
        assert tx.asset1 is not None
        assert tx.type == ThorTxType.TYPE_SWAP

        assert tx.amount1 > 0
        assert tx.amount2 > 0

    tx0 = result.txs[0]
    assert tx0.date == 1613413527
    assert tx0.block_height == 2648585
    assert tx0.asset1 == 'BNB.BNB'
    assert tx0.amount1 == 2274318077 / DIV
    assert tx0.asset2 is None
    assert tx0.amount2 == 70000000000 / DIV
    assert tx0.slip == 0.0009
    assert tx0.fee == 1073372 / DIV


def test_parser_v1_double(example_tx_gen):
    example_tx_list = example_tx_gen(name='v1_dbl_swap.json')

    result = TxParserV1().parse_tx_response(example_tx_list)
    assert len(result.txs) == 50
    assert result.total_count == 135643

    for tx in result.txs:
        assert tx.block_height > 0
        assert tx.date > 0
        assert tx.asset1 is not None
        assert tx.asset2 is not None  # double swap => both not none
        assert tx.type == ThorTxType.TYPE_SWAP

        assert tx.amount1 > 0
        assert tx.amount2 > 0

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

    result = TxParserV1().parse_tx_response(example_tx_list)
    assert len(result.txs) == 42
    assert result.total_count == 21791

    for tx in result.txs:
        assert tx.block_height > 0
        assert tx.date > 0
        assert tx.type == ThorTxType.TYPE_ADD_LIQUIDITY
        assert tx.amount1 > 0 or tx.amount2 > 0
        assert tx.asset1 is not None

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

    result = TxParserV1().parse_tx_response(example_tx_list)
    assert len(result.txs) == 24  # 18 are pending!
    assert result.total_count == 12500

    for tx in result.txs:
        assert tx.block_height > 0
        assert tx.date > 0
        assert tx.type == ThorTxType.TYPE_WITHDRAW
        assert tx.amount1 > 0 and tx.amount2 > 0
        assert tx.asset1 is not None
        assert tx.asset2 is None

    tx0 = result.txs[0]

    assert tx0.asset1 == 'BNB.BTCB-1DE'
    assert tx0.amount1 == pytest.approx(46546272 / DIV)
    assert tx0.asset2 is None
    assert tx0.amount2 == pytest.approx(473485683282 / DIV)
    assert tx0.user_address == 'bnb12nnn740tn4d2n6tyr2kpzqz7qsesl8h8rpjwgs'


def test_parser_v1_add(example_tx_gen):
    example_tx_list = example_tx_gen(name='v1_add.json')

    result = TxParserV1().parse_tx_response(example_tx_list)

    assert len(result.txs) == 36
    assert result.total_count == 36

    for tx in result.txs:
        assert tx.block_height > 0
        assert tx.date > 0
        assert tx.type == ThorTxType.TYPE_ADD
        assert tx.amount1 > 0 or tx.amount2 > 0
        assert tx.asset1 is not None
        assert tx.liq_units == 0 and tx.slip == 0.0 and tx.fee == 0

    tx0 = result.txs[0]

    assert tx0.asset1 == 'BNB.USDT-6D8'
    assert tx0.amount1 == 0.0  # rune only adds in this test
    assert tx0.asset2 is None
    assert tx0.amount2 == pytest.approx(2500000000000 / DIV)


def test_parser_v1_refund(example_tx_gen):
    example_tx_list = example_tx_gen(name='v1_refund.json')

    result = TxParserV1().parse_tx_response(example_tx_list)

    assert len(result.txs) == 13
    assert result.total_count == 3314

    for tx in result.txs:
        assert tx.block_height > 0
        assert tx.date > 0
        assert tx.type == ThorTxType.TYPE_REFUND

    tx0 = result.txs[0]
    assert tx0.user_address == 'bnb143cx0wzff603u29hvvvnq00hmr9tx9p7n4tfdr'
    assert tx0.asset1 == '.'
    assert tx0.amount1 == 0.0
    assert tx0.amount2 == pytest.approx(527077000000 / DIV)
