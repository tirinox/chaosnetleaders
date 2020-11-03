import asyncio
import csv
import logging
from collections import defaultdict
from dataclasses import dataclass

from tqdm.asyncio import tqdm, tqdm_asyncio
from dotenv import load_dotenv
import pandas as pd
from main import init_db
from midgard.models.transaction import BEPTransaction

logging.basicConfig(level=logging.INFO)


@dataclass
class ValueTracker:
    min_v: float = 0.0
    max_v: float = 0.0
    avg_v: float = 0.0
    total_v: int = 0

    def update(self, v, n):
        self.total_v += v
        self.avg_v = self.total_v / n
        self.min_v = min(self.min_v, v)
        self.max_v = max(self.max_v, v)


@dataclass
class PoolMetric:
    name: str = ""

    fee: ValueTracker = ValueTracker()
    slip: ValueTracker = ValueTracker()
    usd_volume: ValueTracker = ValueTracker()
    rune_volume: ValueTracker = ValueTracker()

    n_tx: int = 0
    n_swaps: int = 0
    n_double_swaps: int = 0

    def update(self, tx: BEPTransaction):
        self.name = tx.pool
        self.n_tx += 1
        if tx.is_double:
            self.n_double_swaps += 1
        else:
            self.n_swaps += 1

        self.fee.update(tx.fee, self.n_tx)
        self.slip.update(tx.slip, self.n_tx)
        self.usd_volume.update(tx.usd_volume, self.n_tx)
        self.rune_volume.update(tx.rune_volume, self.n_tx)


def metrics_file(name):
    return f'../../data/metrics/{name}'


async def export_tx_csv(outfile):
    with open(outfile, mode='w') as f:
        writer = csv.writer(f, delimiter='\t', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow([
            'type',
            'date',
            'block_height',
            'pool',
            'input_address',
            'input_asset',
            'input_amount',
            'input_usd_price',
            'output_address',
            'output_asset',
            'output_amount',
            'output_usd_price',
            'rune_volume',
            'usd_volume',
            'fee',
            'slip',
        ])
        n = await BEPTransaction.all_by_date().count()
        with tqdm(total=n) as pbar:
            async for tx in BEPTransaction.all_by_date():
                if tx.rune_volume is not None:
                    writer.writerow([
                        tx.type,
                        tx.date,
                        tx.block_height,
                        tx.pool,
                        tx.input_address,
                        tx.input_asset,
                        tx.input_amount,
                        tx.input_usd_price,
                        tx.output_address,
                        tx.output_asset,
                        tx.output_amount,
                        tx.output_usd_price,
                        tx.rune_volume,
                        tx.usd_volume,
                        tx.fee,
                        tx.slip
                    ])
                pbar.update(1)

async def write_pool_data(outfile):
    pools = defaultdict(PoolMetric)

    async for tx in BEPTransaction.all():
        if tx.rune_volume is not None:
            pools[tx.pool].update(tx)
            pools['all'].update(tx)

    with open(outfile, mode='w') as f:
        writer = csv.writer(f, delimiter='\t', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow([])


def read_csv(name) -> pd.DataFrame:
    return pd.read_csv(name, delimiter='\t', quotechar='"')


async def main():
    await init_db()
    # await write_pool_data('../../data/metrics/by_pool.csv')

    df = read_csv(metrics_file('all_tx.csv'))
    print(df[['fee', 'slip', 'usd_volume']].describe())


# await export_tx_csv(metrics_file('all_tx.csv'))

if __name__ == '__main__':
    load_dotenv('../../.env')
    asyncio.run(main())
