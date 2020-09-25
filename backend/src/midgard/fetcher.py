import aiohttp
import logging
from midgard.models.transaction import BEPTransaction
from midgard.aggregator import fill_rune_volumes
from utils import schedule_task_periodically


URL_SWAP_GEN = lambda off, n: f"https://chaosnet-midgard.bepswap.com/v1/txs?offset={off}&limit={n}&type=swap,doubleSwap"
MIDGARD_TX_BATCH = 50
FETCH_INTERVAL = 60.0


class Fetcher:
    def __init__(self, batch_size, url_generator, session: aiohttp.ClientSession):
        self.batch_size = batch_size
        self.url_generator = url_generator
        self.session = session

    async def get_transaction_list(self, i, n):
        url = self.url_generator(i, n)
        logging.info(f'getting {url}...')
        async with self.session.get(url) as resp:
            json = await resp.json()
            count = int(json['count'])
            models = []
            for i, tx in enumerate(json['txs'], start=1):
                tx_model = BEPTransaction.from_json(tx, order_of_come=i)
                if tx_model is not None:
                    models.append(tx_model)

            return models, count


async def save_transactions(transactions):
    any_new = False
    saved_list = []
    for tx_model in transactions:
        saved = await tx_model.save_unique()
        if saved:
            saved_list.append(tx_model)
        any_new = any_new or saved

    if transactions and not any_new:
        logging.info("all transactions are stale. nothing more to save.")
    return any_new, saved_list


async def fetch_all_transactions(http_session):
    logging.info('fetching all transactions.')
    fetcher = Fetcher(MIDGARD_TX_BATCH, URL_SWAP_GEN, http_session)

    await BEPTransaction.all().delete()

    i = 0
    while True:
        transactions, count = await fetcher.get_transaction_list(i, fetcher.batch_size)
        if not transactions:
            logging.info('no more transactions; break fetching loop')
            break

        await save_transactions(transactions)

        local_count = await BEPTransaction.all().count()
        logging.info(f'added {len(transactions)} transactions start = {i} of {count}; local db has {local_count} transactions')

        i += fetcher.batch_size


BIG_NUMBER = 2 ** 63


def min_date(txs):
    if not txs:
        return BIG_NUMBER
    return min(int(tx.date) for tx in txs)


async def fetch_all_absent_transactions(http_session, verify_date=True):
    new_transactions = []

    fetcher = Fetcher(MIDGARD_TX_BATCH, URL_SWAP_GEN, http_session)

    min_fetched_date = BIG_NUMBER

    i = 0
    while True:
        transactions, midgard_count = await fetcher.get_transaction_list(i, fetcher.batch_size)
        if not transactions:
            logging.info('no more transactions; break fetching loop')
            break

        min_fetched_date = min(min_date(transactions), min_fetched_date)
        # print(f'min_fetched_date = {min_fetched_date}')

        any_new, saved_transactions = await save_transactions(transactions)

        new_transactions += saved_transactions

        max_local_date = await BEPTransaction.last_date()
        # print(f'max_local_date = {max_local_date}')

        if not any_new:
            if verify_date and max_local_date < min_fetched_date:
                logging.warning(f'no new transactions; '
                                f'max_local_date ({max_local_date}) < min_fetched_date({min_fetched_date})! '
                                f'continuing...')
            else:
                logging.info('no new transactions; break fetching loop')
                break
        else:
            local_count = await BEPTransaction.all().count()
            logging.info(
                f'added {len(transactions)} transactions start = {i} of {midgard_count}; '
                f'local db has {local_count} transactions')

        i += fetcher.batch_size

    return new_transactions


async def get_more_transactions_periodically():
    async with aiohttp.ClientSession() as session:
        await fetch_all_absent_transactions(session)
        await fill_rune_volumes()


async def run_fetcher(*_):
    schedule_task_periodically(FETCH_INTERVAL, get_more_transactions_periodically)
