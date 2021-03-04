from dataclasses import dataclass

from aiothornode.connector import ThorConnector, ThorEnvironment, TEST_NET_ENVIRONMENT_MULTI_1, \
    CHAOS_NET_BNB_ENVIRONMENT

from helpers.constants import NetworkIdents


def get_thor_env_by_network_id(network_id) -> ThorEnvironment:
    if network_id == NetworkIdents.TESTNET_MULTICHAIN:
        return TEST_NET_ENVIRONMENT_MULTI_1
    elif network_id == NetworkIdents.CHAOSNET_BEP2CHAIN:
        return CHAOS_NET_BNB_ENVIRONMENT
    else:
        # todo: add multi-chain chaosnet
        raise KeyError('unsupported network ID!')


@dataclass
class ValueFiller:
    thor_connector: ThorConnector
    batch_size: int = 1000
    retries: int = 3

    async def run_job(self):
        ...

# 1. take a limited batch of unfilled tx
