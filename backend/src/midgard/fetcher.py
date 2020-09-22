import aiohttp
import logging
from midgard.models.transaction import BEPTransaction


URL_SWAP_GEN = lambda off, n: f"https://chaosnet-midgard.bepswap.com/v1/txs?offset={off}&limit={n}&type=swap,doubleSwap"
BATCH = 30


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

    if not any_new:
        logging.info("all transactions are stale. nothing more to save.")
    return any_new, saved_list


async def fetch_all_absent_transactions():
    new_transactions = []
    async with aiohttp.ClientSession() as session:
        fetcher = Fetcher(BATCH, URL_SWAP_GEN, session)

        i = 0
        while True:
            transactions, count = await fetcher.get_transaction_list(i, fetcher.batch_size)
            if not transactions:
                logging.info('no more transactions; break fetching loop')
                break

            any_new, saved_transactions = await save_transactions(transactions)

            new_transactions += saved_transactions

            if not any_new:
                logging.info('no new transactions; break fetching loop')
                break
            else:
                logging.info(f'added {len(transactions)} transactions {i} of {count}')
            i += fetcher.batch_size

    return new_transactions
