import aiohttp
import logging
from midgard.models.transaction import BEPTransaction
from midgard.aggregator import fill_rune_volumes
from utils import schedule_task_periodically


URL_SWAP_GEN = lambda off, n: f"https://chaosnet-midgard.bepswap.com/v1/txs?offset={off}&limit={n}&type=swap,doubleSwap"
MIDGARD_TX_BATCH = 50
FETCH_INTERVAL = 60.0
FILL_INTERVAL = 20.0
FETCH_FULL_INTERVAL = 60.0 * 60 * 24  # full scan every day
FETCH_FULL_START_DELAY = 10.0

MAX_TX_TO_FETCH_FULLSCAN = 0  # full-full!


class Fetcher:
    def __init__(self, url_generator, session: aiohttp.ClientSession):
        self.url_generator = url_generator
        self.session = session

    async def get_transaction_list(self, i, n):
        url = self.url_generator(i, n)
        logging.info(f'getting {url}...')
        async with self.session.get(url) as resp:
            json = await resp.json()
            count = int(json['count'])
            models = []
            txs = json['txs']
            for i, tx in enumerate(txs, start=1):
                tx_model = BEPTransaction.from_json(tx)
                if tx_model is not None:
                    models.append(tx_model)

            return models, count, len(txs) > 0


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


async def fetch_all_transactions(http_session, clear=False, max_items_deep=0, start=0):
    logging.info('[FULL SCAN] fetching all transactions.')
    fetcher = Fetcher(URL_SWAP_GEN, http_session)

    if clear:
        logging.warning("[FULL SCAN] clearing all BEPTransaction-s!")
        await BEPTransaction.all().delete()

    i = start
    while True:
        if max_items_deep != 0 and i >= max_items_deep:
            break

        transactions, count, go_on = await fetcher.get_transaction_list(i, MIDGARD_TX_BATCH)
        if not go_on:
            logging.info('[FULL SCAN] no more transactions; break fetching loop')
            break

        _, saved_transactions = await save_transactions(transactions)

        local_count = await BEPTransaction.all().count()
        logging.info(f'[FULL SCAN] added {len(saved_transactions)} transactions start = {i} of {count}; local db has {local_count} transactions')

        i += MIDGARD_TX_BATCH


BIG_NUMBER = 2 ** 63


def min_date(txs):
    if not txs:
        return BIG_NUMBER
    return min(int(tx.date) for tx in txs)


async def fetch_all_absent_transactions(http_session, verify_date=True):
    logging.info('fetching new transactions.')
    new_transactions = []

    fetcher = Fetcher(URL_SWAP_GEN, http_session)

    min_fetched_date = BIG_NUMBER

    i = 0
    while True:
        transactions, midgard_count, go_on = await fetcher.get_transaction_list(i, MIDGARD_TX_BATCH)
        if not go_on:
            logging.info('no more transactions; break fetching loop')
            break

        min_fetched_date = min(min_date(transactions), min_fetched_date)

        any_new, saved_transactions = await save_transactions(transactions)

        new_transactions += saved_transactions

        max_local_date = await BEPTransaction.last_date()

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
                f'added {len(saved_transactions)} transactions start = {i} of {midgard_count}; '
                f'local db has {local_count} transactions')

        i += MIDGARD_TX_BATCH

    return new_transactions


async def get_more_transactions_periodically(full_scan=False, start=0):
    async with aiohttp.ClientSession() as session:
        try:
            if full_scan:
                await fetch_all_transactions(session, max_items_deep=MAX_TX_TO_FETCH_FULLSCAN, start=start)
            else:
                await fetch_all_absent_transactions(session)
        except Exception as e:
            logging.error(f"failed task: get_more_transactions_periodically(full_scal={full_scan}), error = {e}")


async def run_fetcher(*_):
    schedule_task_periodically(FETCH_INTERVAL, get_more_transactions_periodically)
    schedule_task_periodically(FETCH_FULL_INTERVAL, get_more_transactions_periodically, FETCH_FULL_START_DELAY, True)
    schedule_task_periodically(FILL_INTERVAL, fill_rune_volumes)

