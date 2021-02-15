import asyncio
import csv
import logging
import os
from collections import defaultdict
from dataclasses import dataclass

import pandas as pd
from dotenv import load_dotenv
from tqdm.asyncio import tqdm

from api import COMP_END_TIMESTAMP, COMP_START_TIMESTAMP
from main import init_db
from models.transaction import BEPTransaction

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
        print(f'export_tx_csv n = {n}')
        with tqdm(total=n) as pbar:
            async for tx in BEPTransaction.all():
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
                else:
                    print(f'stop! tx is incomplete {tx}')
                    # break
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


def save_csv(name, df: pd.DataFrame):
    df.to_csv(name, sep='\t', index=False)


def tx_only_for_comp(df: pd.DataFrame):
    return df[df['date'].between(COMP_START_TIMESTAMP, COMP_END_TIMESTAMP)]


def add_rank(lb, by):
    ranking = lb[by].rank(ascending=False)
    lb.insert(0, 'rank', ranking)
    return lb.sort_values('rank', ascending=True)


async def export_leaderboard(all_tx: pd.DataFrame):
    print(f'all tx in pd = {len(all_tx)}')
    grouped = all_tx.groupby('input_address', as_index=False)
    rune_volumes: pd.DataFrame = grouped['rune_volume'].sum()

    tx_count = grouped.size()
    rune_volumes['tx_count'] = tx_count['size']
    lb = add_rank(rune_volumes, 'rune_volume')

    usd_volumes = grouped['usd_volume'].sum()
    usd_volumes['tx_count'] = tx_count['size']
    usd_lb = add_rank(usd_volumes, 'usd_volume')

    # print('-' * 100)
    # print('Leader board RUNE')
    # print(lb)
    #
    # print('-' * 100)
    # print('Leader board USD')
    # print(usd_lb)

    save_csv(metrics_file('lb_rune.csv'), lb)
    save_csv(metrics_file('lb_usd.csv'), usd_lb)

    print('unique participants = ', len(all_tx['input_address'].unique()))


def get_stat_for(df: pd.DataFrame, name):
    d = df[name].describe().to_dict()
    del d['count']
    return {f"{name}_{k}": v for k, v in d.items()}


def process_pool(pool_name, df: pd.DataFrame):
    n = len(df)
    full_d = {
        'pool': pool_name,
        'n_swaps': n,
        **get_stat_for(df, 'rune_volume'),
        **get_stat_for(df, 'usd_volume'),
        **get_stat_for(df, 'fee'),
        **get_stat_for(df, 'slip'),
        'r_swaps': len(df[df["type"] == BEPTransaction.TYPE_SWAP]) / n,
        'r_double_swaps': len(df[df["type"] == BEPTransaction.TYPE_DOUBLE_SWAP]) / n,
    }
    return full_d


async def main():
    await init_db()

    # Make CSV for all transactions
    path_all_tx = metrics_file('all_tx.csv')
    if not os.path.exists(path_all_tx):
        await export_tx_csv(path_all_tx)

    all_tx_df = read_csv(path_all_tx)
    print(f'all_tx_df len = {len(all_tx_df)}')

    # Competition TX only:
    comp_tx_df = tx_only_for_comp(all_tx_df)
    await export_leaderboard(comp_tx_df)

    # Split by pools and add "ALL" pool
    pool_names = comp_tx_df.pool.unique()
    pools_df = {
        name: comp_tx_df[comp_tx_df['pool'] == name] for name in pool_names
    }
    pools_df['all'] = comp_tx_df

    pool_stats = pd.DataFrame([process_pool(name, df) for name, df in pools_df.items()])

    save_csv(metrics_file('pool.csv'), pool_stats)


if __name__ == '__main__':
    load_dotenv('../../../.env')
    asyncio.run(main())
