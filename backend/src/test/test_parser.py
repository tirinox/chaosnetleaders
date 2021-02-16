import json
import os
from jobs.tx.parser import TxParserV1

LIST_OF_EXAMPLE = (
    'v1_add.json',
    'v1_dbl_swap.json',
    'v1_refund.json',
    'v1_stake_unstake.json',
    'v1_swap.json',
)

PATH = './tx_examples'


def load_tx_list(name):
    with open(os.path.join(PATH, name), 'r') as f:
        txs = json.load(f)
    return txs


if __name__ == '__main__':
    txs = load_tx_list(LIST_OF_EXAMPLE[1])
    result = TxParserV1().parse_tx_response(txs)
    print(result)
