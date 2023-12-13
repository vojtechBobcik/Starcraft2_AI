from sc2 import maps
from sc2.player import Bot, Computer
from sc2.main import run_game
from sc2.data import Race, Difficulty
from sc2.bot_ai import BotAI
from sc2.constants import *
from sc2.bot_ai import BotAI, Race
from sc2.data import Result
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2
from typing import List, Optional


rt = False
class Bo_bot(BotAI):
    NAME: str = "MarineRushBot"
    RACE: Race = Race.Terran
    
    
    async def on_step(self, iteration: int):
        # Jestliže mám Command Center
        if self.townhalls:
            # První Command Center
            cc = self.townhalls[0]
            
            
            """ if enemy_SCV.closer_than(7,cc).amount>=1:
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

            ccForSCV = self.townhalls.random 
            if self.can_afford(UnitTypeId.SCV) and self.supply_workers <= max_scvs and ccForSCV.is_idle:
                ccForSCV.train(UnitTypeId.SCV)
            
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

            # Postav Supply Depot, jestliže zbývá méně než 6 supply a je využito více než 13
            if self.supply_left < 6 and self.supply_used >= 14 and not self.already_pending(UnitTypeId.SUPPLYDEPOT):
                if self.can_afford(UnitTypeId.SUPPLYDEPOT):
                    # Budova bude postavena poblíž Command Center směrem ke středu mapy
                    # SCV pro stavbu bude vybráno automaticky viz dokumentace
                    
                    vaspenes = self.vespene_geyser.closer_than(20.0, cc)
                    
                    await self.build(
                        UnitTypeId.SUPPLYDEPOT,
                        near=vaspenes.random.position.towards_with_random_angle(self.game_info.map_center, 3)
                        )


            # Stavba Barracks
            # Bot staví tak dlouho, dokud si může dovolit stavět Barracks a jejich počet je menší než 6
            if self.tech_requirement_progress(UnitTypeId.BARRACKS) == 1:
                # Je jich méně než 6 nebo se již nějaké nestaví
                if self.structures(UnitTypeId.BARRACKS).amount < 6:
                    if self.can_afford(UnitTypeId.BARRACKS) and not self.already_pending(UnitTypeId.BARRACKS):
                        
                        if self.structures(UnitTypeId.BARRACKS).amount<2:
                            await self.build(
                                building=UnitTypeId.BARRACKS,
                                near=cc.position.towards(self.game_info.map_center, 8), 
                                placement_step=6,
                                max_distance=25)
                        elif self.structures(UnitTypeId.REFINERY).amount==1 and self.structures(UnitTypeId.BARRACKS).amount<4:
                            await self.build(
                                building=UnitTypeId.BARRACKS,
                                near=self.structures(UnitTypeId.REFINERY)[0].position.towards(self.main_base_ramp.top_center.position, 8), 
                                placement_step=6,
                                max_distance=25
                                )
                        elif self.structures(UnitTypeId.REFINERY).amount==2 and self.structures(UnitTypeId.BARRACKS).amount<6:
                            await self.build(
                                building=UnitTypeId.BARRACKS,
                                near=self.structures(UnitTypeId.REFINERY)[1].position.towards(self.main_base_ramp.top_center.position, 8), 
                                placement_step=6,
                                max_distance=25
                                )
                            
                        """ elif self.structures(UnitTypeId.COMMANDCENTER).amount==2:
                            await self.build(
                                UnitTypeId.BARRACKS,
                                near=self.structures(UnitTypeId.COMMANDCENTER)[1].position.towards(self.game_info.map_center, 8), placement_step=6) """

            
            
            # Trénování jednotek:
            # Pouze, má-li bot postavené Barracks a může si jednotku dovolit
            if self.structures(UnitTypeId.BARRACKS):
                # Každá budova Barracks trénuje v jeden čas pouze jednu jednotku (úspora zdrojů)
                if self.units(UnitTypeId.MARINE).amount <25:
                    self.all_barrack_train(UnitTypeId.MARINE)
                    
                else:
                    self.all_barrack_train(UnitTypeId.MARAUDER)
            #Vytrenovani siegeTanků 
            if self.structures(UnitTypeId.FACTORY).exists and self.units(UnitTypeId.SIEGETANK).amount<6:
                await self.all_factory_train(UnitTypeId.SIEGETANK)
            await self.manage_tanks()
                    

                    

            # Útok s jednotkou Marine
            # Má-li bot více než 15 volných jednotek Marine, zaútočí na náhodnou nepřátelskou budovu nebo se přesune na jeho startovní pozici
            typeListOfDefendingUnits = [UnitTypeId.MARINE, UnitTypeId.MARAUDER, UnitTypeId.SIEGETANK]
            if self.enemy_units(UnitTypeId.SCV).closer_than(15,cc).amount>=2:
                if self.units(typeListOfDefendingUnits).amount<1:
                    defendingSCVs = self.units(UnitTypeId.SCV)
                    for defendingUnit in defendingSCVs:
                        defendingUnit.attack(self.enemy_units.closest_to(cc))
                else:
                    UnitsThatDefend = self.units(typeListOfDefendingUnits)
                    for defendingUnit in UnitsThatDefend:
                        defendingUnit.attack(self.enemy_units.visible.random)
            elif self.enemy_units.visible.amount>=1 and self.units(typeListOfDefendingUnits).amount>1:
                    for defendingUnit in self.units(typeListOfDefendingUnits):
                        defendingUnit.attack(self.enemy_units.visible.random)
                        
            elif self.units(UnitTypeId.MARINE).amount>=18 and self.units(UnitTypeId.MARAUDER).amount>=10 and self.units(UnitTypeId.SIEGETANK).amount>=4:
                
                await self.attackWithUnit(UnitTypeId.MARINE)
                await self.attackWithUnit(UnitTypeId.MARAUDER)
                await self.attackWithUnit(UnitTypeId.SIEGETANK)

            #upgrade basek
            for b in self.townhalls:
                await self.upgradeMainBase(b, AbilityId.UPGRADETOPLANETARYFORTRESS_PLANETARYFORTRESS)
                
            # Stavba EngineeringBay pokud 
            if self.structures(UnitTypeId.ENGINEERINGBAY).amount < 1  and self.can_afford(UnitTypeId.ENGINEERINGBAY) and not self.already_pending(UnitTypeId.ENGINEERINGBAY):
                await self.build(
                            UnitTypeId.ENGINEERINGBAY,
                            near=cc.position.towards(self.game_info.map_center, 8))
            
                
            # vyzkum zbrani    
            if self.structures(UnitTypeId.ENGINEERINGBAY).amount==1 and self.can_afford(AbilityId.RESEARCH_TERRANINFANTRYWEAPONS):
                self.do(self.structures(UnitTypeId.ENGINEERINGBAY).first(AbilityId.RESEARCH_TERRANINFANTRYWEAPONS))
                
            await self.upgrade_barracs()
            
            #Postavení factory
            if self.townhalls.amount>1 and self.structures(UnitTypeId.REFINERY).amount==2:
               await self.BuildFactory(self.townhalls[1])
               await self.upgrade_factory()
                
            #Postavení nových commandcenter
            if self.structures(UnitTypeId.BARRACKS).amount>=2 and self.structures(UnitTypeId.COMMANDCENTER).amount<=3 and self.can_afford(UnitTypeId.COMMANDCENTER) and not self.already_pending(UnitTypeId.COMMANDCENTER):
                worker = self.workers.random
                if worker:
                    worker.build(UnitTypeId.COMMANDCENTER, await self.get_next_expansion())
            
            for c in self.townhalls:
                if c.health_percentage<75:
                    worker = self.select_build_worker(c.position)
                    if worker is None:
                        break
                    if c is None:
                        break
                    if c.distance_to(self.enemy_start_locations[0])>20:
                        worker.repair(c)
                
          
        
    def all_barrack_train(self, unitType):
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
        for factory in self.structures(UnitTypeId.FACTORY).ready.idle:
            if self.can_afford(AbilityId.BUILD_TECHLAB_FACTORY) and not factory.has_add_on:
                factory.build(UnitTypeId.FACTORYTECHLAB)
        
        
                
    async def upgradeMainBase(self,mainBase,upgrade):
        if self.can_afford(upgrade):
            self.do(mainBase(upgrade))
        
        
    
    async def BuildFactory(self,where):
        if self.tech_requirement_progress(UnitTypeId.FACTORY) == 1:
            
            """ if self.structures(UnitTypeId.FACTORY).amount < 2:
                if self.can_afford(UnitTypeId.FACTORY) and not self.already_pending(UnitTypeId.FACTORY):
                    placePos = self.townhalls[-1].position.towards(self.game_info.map_center, 5)
                    if self.in_placement_grid(pos= placePos):
                        await self.build(
                            UnitTypeId.FACTORY,
                            near=self.townhalls[-1].position.towards(self.game_info.map_center, 5), placement_step=5)
                    else:
                        await self.build(
                            UnitTypeId.FACTORY,
                            near=self.structures(UnitTypeId.BARRACKS)[-1].position.towards(self.game_info.map_center, 5), placement_step=5) """
                        
            if self.structures(UnitTypeId.FACTORY).amount < 3:
                if self.can_afford(UnitTypeId.FACTORY) and not self.already_pending(UnitTypeId.FACTORY):
                    await self.build(
                        UnitTypeId.FACTORY,
                        near=where.position.towards(self.game_info.map_center,5), placement_step=6)
                    
    
    async def attackWithUnit(self, choosenUnit):
        # Útok s jednotkou Marine
            # Má-li bot více než 15 volných jednotek Marine, zaútočí na náhodnou nepřátelskou budovu nebo se přesune na jeho startovní pozici
        idle_units = self.units(choosenUnit).idle
        
        target = self.enemy_structures.random_or(
            self.enemy_start_locations[0]).position
        for attacking_unit in idle_units:
            attacking_unit.attack(target)
    
    async def PatrolWithUnit(self, choosenUnit, patrolTo):
        # Útok s jednotkou Marine
            # Má-li bot více než 15 volných jednotek Marine, zaútočí na náhodnou nepřátelskou budovu nebo se přesune na jeho startovní pozici
        idle_units = self.units(choosenUnit).idle
    
        for patroling_unit in idle_units:
            patroling_unit.patrol(patrolTo)
    
    """ async def MoveArtilery(self):
        tanks = self.units(UnitTypeId.SIEGETANK)
        for t in tanks:
            self.do(t.move(self.structures.closest_distance_to(self.game_info.map_center.position)))
            
    async def SetUpArtilery(self):
        tanks = self.units(UnitTypeId.SIEGETANK)
        for t in tanks:
            while t.is_moving:
                pass
            self.do(t(AbilityId.SIEGEMODE_SIEGEMODE)) """
            
    async def manage_tanks(self):
        
        for tank in self.units(UnitTypeId.SIEGETANK):
            if self.enemy_units.in_attack_range_of(tank) or self.enemy_structures.in_attack_range_of(tank):
                tank(AbilityId.SIEGEMODE_SIEGEMODE)

        for tank in self.units(UnitTypeId.SIEGETANKSIEGED):
            if not self.enemy_units.in_attack_range_of(tank) and not self.enemy_structures.in_attack_range_of(tank):
                tank(AbilityId.UNSIEGE_UNSIEGE)
                

        
                
        
    
run_game(maps.get("sc2-ai-cup-2022"), [
    #Bot(Race.Terran, WorkerRushBot()),
    Bot(Race.Terran, Bo_bot()),
    Computer(Race.Terran, Difficulty.Medium)
    
], realtime=False)



    
