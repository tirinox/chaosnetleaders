from helpers.db import db


# v1 (chaosnet)
# https://chaosnet-midgard.bepswap.com/v1/txs?asset=USDT-6D8&offset=400&limit=50&type=swap,doubleSwap
#

# v2 (multinet)
# https://testnet.midgard.thorchain.info/v2/actions?limit=10&offset=100
# swap, addLiquidity, withdraw, donate, refund


class ThorTransaction(db.Model):
    TYPE_ADD = 'add'
    TYPE_SWAP = 'swap'
    TYPE_WITHDRAW = 'withdraw'
    TYPE_DONATE = 'donate'
    TYPE_REFUND = 'refund'

    __tablename__ = 'thor_tx'

    id = db.Column(db.BigInteger, primary_key=True)
    hash = db.Column(db.String(128), key=True, unique=True)
    height = db.Column(db.BigInteger, default=0)

    type = db.Column(db.String(20), key=True)
    pool1 = db.Column(db.String(32), key=True)
    pool2 = db.Column(db.String(32), key=True, default=None)

    input_address = db.Column(db.String(64), key=True)
    input_asset = db.Column(db.String(32), key=True)
    input_amount = db.Column(db.Float, default=0.0)
    input_usd_price = db.Column(db.Float, default=0.0)

    output_address = db.Column(db.String(64), key=True)
    output_asset = db.Column(db.String(32), key=True)
    output_amount = db.Column(db.Float, default=0.0)
    output_usd_price = db.Column(db.Float, default=0.0)

    rune_total = db.Column(db.Float, default=0.0)
    usd_total = db.Column(db.Float, default=0.0)

    fee = db.Column(db.Float, default=0.0)
    slip = db.Column(db.Float, default=0.0)
