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
    
    first_wave =False
    async def on_step(self, iteration: int):
        # Jestliže mám Command Center
        if self.townhalls:
            # První Command Center
            cc = self.townhalls[0]
            
            for depo in self.structures(UnitTypeId.SUPPLYDEPOT).ready:
                self.do(depo(AbilityId.MORPH_SUPPLYDEPOT_LOWER))

            # Trénování SCV
            # Bot trénuje nová SCV, jestliže je jich méně než 17 (max_scvs) zvyšuje se počtem refinery
            max_scvs = 16

            #Postav refinery na geysirech blizsich nez 20 od CC
            vaspenes = self.vespene_geyser.closer_than(20.0, cc)
            if vaspenes is not None and self.structures(UnitTypeId.BARRACKS).amount > 3:    
                for vaspene in vaspenes:
                    if not self.can_afford(UnitTypeId.REFINERY):
                        break
                    worker = self.select_build_worker(vaspene.position)
                    if worker is None:
                        break
                    if not self.units(UnitTypeId.REFINERY).closer_than(1.0, vaspene).exists and self.structures(UnitTypeId.REFINERY).amount<1 and not self.already_pending(UnitTypeId.REFINERY):
                        await self.build(UnitTypeId.REFINERY, vaspene)
                        max_scvs = max_scvs + self.structures(UnitTypeId.REFINERY).amount * 3
                        break


            if self.can_afford(UnitTypeId.SCV) and self.supply_workers <= max_scvs and cc.is_idle:
                cc.train(UnitTypeId.SCV)
            
            # Zbylé SCV bot pošle těžit minerály nejblíže Command Center
                #zacnu resit az mam rafinerky
                #prochazim rafinerky, ktere postupne zaplnuju
            if self.structures(UnitTypeId.REFINERY).ready.amount > 0: 
                if cc.assigned_harvesters > cc.ideal_harvesters or self.idle_worker_count > 0:
                    for r in self.structures(UnitTypeId.REFINERY):
                        # TODO2x assigned < ideal
                        if r.assigned_harvesters < r.ideal_harvesters and self.idle_worker_count > 0 :
                            idle_SCVs=[x for x in self.units(UnitTypeId.SCV).idle]
                            for idle_SCV in idle_SCVs:
                                idle_SCV.gather(r)
                            
                        # TODO 2x assigned < ideal        
                        if r.assigned_harvesters < r.ideal_harvesters :
                            #TODO ziskat harvestory co aktualne pracuju na mineraloch a jendoho z nich vzit
                            # HELP - udelat si napr 3 pole. jedno pole vsech harvestoru, druhe pole harvestoru na mineraloch a treti na gas. 
                            # PROBLEM - co udela harvestor po tom co se vytvori.. proste nekam automaticky jde.. je potreba ho odchytit
                            w = self.workers.closest_to(cc)
                            w.gather(r)
                        if r.assigned_harvesters > r.ideal_harvesters:
                            #w = self.workers.collecting()
                            #w.gather(self.mineral_field.closest_to(cc))
                            pass
            else:
                for scv in self.workers.idle:
                    scv.gather(self.mineral_field.closest_to(cc))
            
            """ if self.structures(UnitTypeId.REFINERY).ready.amount > 0: #zacnu resit az mam rafinerky
                mineral_workers=[]
                gas_workers=[]
                if self.assignBots:
                    free_workers=[]
                    free_workers.append(self.workers.idle)
                    self.assignBots=False

                for r in self.structures(UnitTypeId.REFINERY):
                    for x in free_workers:
                        if len(gas_workers)<r.ideal_harvesters:
                            gas_workers.append(x)
                            x.gather(r)
                        if len(mineral_workers)<cc.ideal_harvesters:
                            mineral_workers.append(x)
                            x.gather(self.mineral_field.closest_to(cc))

                    
                    if self.idle_worker_count > 0 :
                        idle_SCVs=[x for x in self.units(UnitTypeId.SCV).idle]
                        for idle_SCV in idle_SCVs:
                            mineral_workers.append(idle_SCV) """
                    

                

            # Postav Supply Depot, jestliže zbývá méně než 6 supply a je využito více než 13
            if self.supply_left < 6 and self.supply_used >= 14 and not self.already_pending(UnitTypeId.SUPPLYDEPOT):
                if self.can_afford(UnitTypeId.SUPPLYDEPOT):
                    # Budova bude postavena poblíž Command Center směrem ke středu mapy
                    # SCV pro stavbu bude vybráno automaticky viz dokumentace
                    await self.build(
                        UnitTypeId.SUPPLYDEPOT,
                        near=cc.position.towards(self.game_info.map_center, 8))


            # Stavba Barracks
            # Bot staví tak dlouho, dokud si může dovolit stavět Barracks a jejich počet je menší než 6
            if self.tech_requirement_progress(UnitTypeId.BARRACKS) == 1:
                # Je jich méně než 6 nebo se již nějaké nestaví
                if self.structures(UnitTypeId.BARRACKS).amount < 6:
                    if self.can_afford(UnitTypeId.BARRACKS) and not self.already_pending(UnitTypeId.BARRACKS):
                        await self.build(
                            UnitTypeId.BARRACKS,
                            near=cc.position.towards(self.game_info.map_center, 8))
                        print(self.get_available_abilities(UnitTypeId.BARRACKS).__name__)

            
            
            # Trénování jednotek:
            # 18 marine
            # 6 marauder
            # Pouze, má-li bot postavené Barracks a může si jednotku dovolit
            if self.structures(UnitTypeId.BARRACKS):
                # Každá budova Barracks trénuje v jeden čas pouze jednu jednotku (úspora zdrojů)
                if self.units(UnitTypeId.MARINE).amount <18:
                    self.all_barrack_train(UnitTypeId.MARINE)
                else:
                    self.all_barrack_train(UnitTypeId.REAPER)
                

            # Útok s jednotkou Marine
            # Má-li bot více než 15 volných jednotek Marine, zaútočí na náhodnou nepřátelskou budovu nebo se přesune na jeho startovní pozici
            idle_marines = self.units(UnitTypeId.MARINE).idle
            idle_reapers = self.units(UnitTypeId.REAPER).idle
            if idle_marines.amount > 18 and idle_reapers.amount >6:
                target = self.enemy_structures.random_or(
                    self.enemy_start_locations[0]).position
                for marine in idle_marines:
                    marine.attack(target)
                for reaper in   idle_reapers:
                    reaper.attack(target)
            


            
            # Stavba EngineeringBay pokud 
            if self.structures(UnitTypeId.ENGINEERINGBAY).amount < 1  and self.can_afford(UnitTypeId.ENGINEERINGBAY) and not self.already_pending(UnitTypeId.ENGINEERINGBAY) and self.units(UnitTypeId.MARINE).idle.amount>10:
                await self.build(
                            UnitTypeId.ENGINEERINGBAY,
                            near=cc.position.towards(self.game_info.map_center, 8))
            
                
            if self.structures(UnitTypeId.ENGINEERINGBAY).amount==1 and self.can_afford(AbilityId.RESEARCH_TERRANINFANTRYWEAPONS):
                engineeringBay = self.structures(UnitTypeId.ENGINEERINGBAY).first
                self.do(engineeringBay(AbilityId.RESEARCH_TERRANINFANTRYWEAPONS))
                
            #if self.structures(UnitTypeId.BARRACKS).amount==1 and self.can_afford(AbilityId.research_terran):
                #self.do(self.structures(UnitTypeId.ENGINEERINGBAY).first(AbilityId.RESEARCH_TERRANINFANTRYWEAPONS))
                #pass

                
    def all_barrack_train(self, unitType):
        if self.can_afford(unitType):
            for barrack in self.structures(UnitTypeId.BARRACKS).idle:
                barrack.train(unitType)                

run_game(maps.get("sc2-ai-cup-2022"), [
    Bot(Race.Terran, Bo_bot()),
    Computer(Race.Terran, Difficulty.Easy)
], realtime=False)



    
