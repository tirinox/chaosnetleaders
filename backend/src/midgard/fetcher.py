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
            for tx in json['txs']:
                tx_model = BEPTransaction.from_json(tx)
                if tx_model is not None:
                    models.append(tx_model)

            return models, count


async def save_transactions(transactions):
    any_new = False
    for tx_model in transactions:
        saved = await tx_model.save_unique()
        any_new = any_new or saved

    if not any_new:
        logging.info("all transactions are stale. nothing more to save.")
    return any_new


async def foo_test():
    async with aiohttp.ClientSession() as session:
        fetcher = Fetcher(BATCH, URL_SWAP_GEN, session)

        i = 0
        while True:
            transactions, count = await fetcher.get_transaction_list(i, fetcher.batch_size)
            if not transactions:
                logging.info('no more transactions; break fetching loop')
                break

            any_new = await save_transactions(transactions)
            if not any_new:
                logging.info('no new transactions; break fetching loop')
                break
            else:
                logging.info(f'added {len(transactions)} transactions (i = {i})')
            i += fetcher.batch_size

        # for i in range(BATCH, count + 1, BATCH):
        #     await get_piece(i, BATCH, session)
