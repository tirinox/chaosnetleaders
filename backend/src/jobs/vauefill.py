from dataclasses import dataclass

from aiohttp import ClientSession
from aiothornode.connector import ThorConnector


@dataclass
class ValueFiller:
    session: ClientSession
    thor_connector: ThorConnector

    async def run_job(self):
        ...


# 1. take a limited batch of unfilled tx
