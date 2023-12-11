from sc2 import maps
from sc2.player import Bot, Computer
from sc2.main import run_game
from sc2.data import Race, Difficulty
from sc2.bot_ai import BotAI
from sc2.constants import *
from sc2.bot_ai import BotAI, Race
from sc2.data import Result
from sc2.ids.unit_typeid import UnitTypeId


class Bo_bot(BotAI):
    NAME: str = "MarineRushBot"
    RACE: Race = Race.Terran
    
    
    async def on_step(self, iteration: int):
        # Jestliže mám Command Center
        if self.townhalls:
            # První Command Center
            cc = self.townhalls[0]
            """ enemy_SCV = self.enemy_units(UnitTypeId.SCV)
            
            if enemy_SCV.closer_than(7,self.structures).amount>=1:
                close_enemy_scv = enemy_SCV.closer_than(7,cc)
                for worker in self.workers:
                    worker.attack(close_enemy_scv)
            else:
                await self.distribute_workers() """
            await self.distribute_workers()

            for depo in self.structures(UnitTypeId.SUPPLYDEPOT).ready:
                self.do(depo(AbilityId.MORPH_SUPPLYDEPOT_LOWER))

            # Trénování SCV
            # Bot trénuje nová SCV, jestliže je jich méně než 17 (max_scvs) zvyšuje se počtem refinery
            max_scvs = 17
            max_scvs = max_scvs + (self.structures(UnitTypeId.REFINERY).amount * 3) + (self.structures(UnitTypeId.COMMANDCENTER).amount * 10)-10

            

            #Postav refinery na geysirech blizsich nez 20 od CC
            vaspenes = self.vespene_geyser.closer_than(20.0, cc)
            if vaspenes is not None and self.structures(UnitTypeId.BARRACKS).amount > 1:    
                for vaspene in vaspenes:
                    if not self.can_afford(UnitTypeId.REFINERY):
                        break
                    worker = self.select_build_worker(vaspene.position)
                    if worker is None:
                        break
                    if not self.units(UnitTypeId.REFINERY).closer_than(1.0, vaspene).exists and self.structures(UnitTypeId.REFINERY).amount<2 and not self.already_pending(UnitTypeId.REFINERY):
                        await self.build(UnitTypeId.REFINERY, vaspene)
                        break

            if self.can_afford(UnitTypeId.SCV) and self.supply_workers <= max_scvs and cc.is_idle:
                cc.train(UnitTypeId.SCV)

            # Postav Supply Depot, jestliže zbývá méně než 6 supply a je využito více než 13
            
            depot_placement_positions = self.main_base_ramp.corner_depots
            
            depots = self.units(UnitTypeId.SUPPLYDEPOT) | self.units(UnitTypeId.SUPPLYDEPOTLOWERED)
            
            # Filter locations close to finished supply depots
            if depots:
                depot_placement_positions = {d for d in depot_placement_positions if depots.closest_distance_to(d) > 1}
                
            # Build depots
            if self.can_afford(UnitTypeId.SUPPLYDEPOT) and not self.already_pending(UnitTypeId.SUPPLYDEPOT):
                if len(depot_placement_positions) == 0:
                    return
                # Choose any depot location
                target_depot_location = depot_placement_positions.pop()
                ws = self.workers.gathering
                if ws: # if workers were found
                    w = ws.random
                    self.do(w.build(UnitTypeId.SUPPLYDEPOT, target_depot_location))
                
            """ if self.supply_left < 6 and self.supply_used >= 14 and not self.already_pending(UnitTypeId.SUPPLYDEPOT):
                if self.can_afford(UnitTypeId.SUPPLYDEPOT):
                    # Budova bude postavena poblíž Command Center směrem ke středu mapy
                    # SCV pro stavbu bude vybráno automaticky viz dokumentace
                    await self.build(
                        UnitTypeId.SUPPLYDEPOT,
                        near=cc.position.towards(self.game_info.map_center, 1)
                        ) """

            # Stavba Barracks
            # Bot staví tak dlouho, dokud si může dovolit stavět Barracks a jejich počet je menší než 6
            if self.tech_requirement_progress(UnitTypeId.BARRACKS) == 1:
                # Je jich méně než 6 nebo se již nějaké nestaví
                if self.structures(UnitTypeId.BARRACKS).amount < 6:
                    if self.can_afford(UnitTypeId.BARRACKS) and not self.already_pending(UnitTypeId.BARRACKS):
                        await self.build(
                            UnitTypeId.BARRACKS,
                            near=cc.position.towards(self.game_info.map_center, 5), placement_step=5)

            # Trénování jednotek:
            # 18 marine
            # 6 marauder
            # Pouze, má-li bot postavené Barracks a může si jednotku dovolit
            if self.structures(UnitTypeId.BARRACKS).exists:
                # Každá budova Barracks trénuje v jeden čas pouze jednu jednotku (úspora zdrojů)
                if self.units(UnitTypeId.MARINE).amount <18 :
                    await self.all_barrack_train(UnitTypeId.MARINE)
                else:
                    await self.all_barrack_train(UnitTypeId.MARAUDER)

            # Útok s jednotkou Marine
            # Má-li bot více než 15 volných jednotek Marine, zaútočí na náhodnou nepřátelskou budovu nebo se přesune na jeho startovní pozici
            idle_marines = self.units(UnitTypeId.MARINE).idle
            if idle_marines.amount > 18:
                target = self.enemy_structures.random_or(self.enemy_start_locations[0]).position
                for marine in idle_marines:
                    marine.attack(target)

            
            # Stavba EngineeringBay pokud 
            if self.structures(UnitTypeId.ENGINEERINGBAY).amount < 1  and self.can_afford(UnitTypeId.ENGINEERINGBAY) and not self.already_pending(UnitTypeId.ENGINEERINGBAY) and self.units(UnitTypeId.MARINE).idle.amount>10:
                await self.build(
                            UnitTypeId.ENGINEERINGBAY,
                            near=cc.position.towards(self.game_info.map_center, 8))
            
            # vyzkum zbrani    
            if self.structures(UnitTypeId.ENGINEERINGBAY).amount==1 and self.can_afford(AbilityId.RESEARCH_TERRANINFANTRYWEAPONS):
                self.do(self.structures(UnitTypeId.ENGINEERINGBAY).first(AbilityId.RESEARCH_TERRANINFANTRYWEAPONS))
                
            """ await self.upgrade_barracs() """
            
            #Postavení factory
            if self.structures(UnitTypeId.BARRACKS).amount>2:
               await self.createFactory()
               await self.upgrade_factory()
                
                
            #Postavení nových commandcenter
            if self.structures(UnitTypeId.BARRACKS).amount>=4 and self.structures(UnitTypeId.COMMANDCENTER).amount<2 and self.can_afford(UnitTypeId.COMMANDCENTER) and not self.already_pending(UnitTypeId.COMMANDCENTER):
                worker = self.workers.gathering.random
                if worker:
                    worker.build(UnitTypeId.COMMANDCENTER, await self.get_next_expansion())
           
           #Vytrenovani siegeTanků 
            if self.structures(UnitTypeId.FACTORY).exists and self.units(UnitTypeId.SIEGETANK).amount<6:
                await self.all_factory_train(UnitTypeId.SIEGETANK)

                
                
    async def all_barrack_train(self, unitType):
        if self.can_afford(unitType):
            for barrack in self.structures(UnitTypeId.BARRACKS).idle:
                barrack.train(unitType)
                
    async def all_factory_train(self, unitType):
        if self.can_afford(unitType):
            for factory in self.structures(UnitTypeId.FACTORY).idle:
                factory.train(unitType) 

    async def upgrade_barracs(self):
        for i,barrack in enumerate(self.structures(UnitTypeId.BARRACKS)):
            if i%2 == 1:
                if self.can_afford(AbilityId.BUILD_REACTOR_BARRACKS):
                    self.do(barrack(AbilityId.BUILD_REACTOR_BARRACKS))
            else:
                if self.can_afford(AbilityId.BUILD_TECHLAB_BARRACKS):
                    self.do(barrack(AbilityId.BUILD_TECHLAB_BARRACKS))
    
    async def upgrade_factory(self):
        for factory in self.structures(UnitTypeId.FACTORY):
            if self.can_afford(AbilityId.BUILD_TECHLAB_FACTORY):
                self.do(factory(AbilityId.BUILD_TECHLAB_FACTORY))
            
    async def createFactory(self):
        if self.tech_requirement_progress(UnitTypeId.FACTORY) == 1:
            # Je jich méně než 6 nebo se již nějaké nestaví
            if self.structures(UnitTypeId.FACTORY).amount < 2:
                if self.can_afford(UnitTypeId.FACTORY) and not self.already_pending(UnitTypeId.FACTORY):
                    await self.build(
                        UnitTypeId.FACTORY,
                        near=self.townhalls[0].position.towards(self.game_info.map_center, 5), placement_step=5)
    
    
    
        
    
run_game(maps.get("sc2-ai-cup-2022"), [
    #Bot(Race.Terran, WorkerRushBot()),
    Bot(Race.Terran, Bo_bot()),
    Computer(Race.Terran, Difficulty.Easy)
    
], realtime=False)



    
