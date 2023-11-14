from sc2 import maps
from sc2.player import Bot, Computer
from sc2.main import run_game
from sc2.data import Race, Difficulty
from sc2.bot_ai import BotAI
from sc2.constants import *


class Bo_bot(BotAI):
    NAME: str = "Bo_bot"
    RACE: Race = Race.Terran

    async def on_step(self, iteration: int):
        await self.distribute_workers()

        # make scvs until 18, usually you only need 1:1 mineral:gas ratio for reapers, but if you don't lose any then you will need additional depots (mule income should take care of that)
        # stop scv production when barracks is complete but we still have a command cender (priotize morphing to orbital command)
        if self.can_afford(UnitTypeId.SCV) and self.supply_left > 0 and self.units(UnitTypeId.SCV).amount < 18 and (self.units(UnitTypeId.BARRACKS).ready.amount < 1 and self.units(UnitTypeId.COMMANDCENTER).idle.exists or self.units(UnitTypeId.ORBITALCOMMAND).idle.exists):
            for th in self.townhalls.idle:
                self.combinedActions.append(th.train(UnitTypeId.SCV))

    async def build_workers(self):
        for commandCenter in self.units(UnitTypeId.COMMANDCENTER).ready.noqueue:
            if self.can_afford(UnitTypeId.SCV):
                await self.do(commandCenter.train(UnitTypeId.SCV))







run_game(maps.get("sc2-ai-cup-2022"), [
    Bot(Race.Terran, Bo_bot()),
    Computer(Race.Terran, Difficulty.Easy)
], realtime=True)