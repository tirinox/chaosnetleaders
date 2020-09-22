from midgard.models.transaction import BEPTransaction
from midgard.models.leader import BEPLeader


class LeaderAggregator:
    RUNE_SYMBOL = 'BNB.RUNE-B1A'

    def __init__(self):
        self.leader_cache = {}

    async def add_transaction(self, tr: BEPTransaction):
        address = tr.input_address
        simple_swap = self.RUNE_SYMBOL in (tr.input_asset, tr.output_asset)
        asset = self.RUNE_SYMBOL if simple_swap else tr.input_asset
        if simple_swap:
            amount = tr.input_amount if tr.input_asset == self.RUNE_SYMBOL else tr.output_amount
        else:
            amount = tr.input_amount

        key = f"{tr.input_address}.{asset}"
        record: BEPLeader = self.leader_cache.get(key)
        if not record:
            record = await BEPLeader.filter(asset=asset, address=address).first()

        if not record:
            record = await BEPLeader.create(asset=asset,
                                            address=address,
                                            amount=amount,
                                            order_of_come=tr.order_of_come,
                                            date=tr.date,
                                            last_tx_id=tr.id)

        self.leader_cache[key] = record

        if tr.date < record.date:
            return
        if tr.date == record.date:
            if tr.order_of_come <= record.order_of_come:
                return

        record.amount += amount

    async def save_all(self):
        for leader in self.leader_cache.values():
            await leader.save()
