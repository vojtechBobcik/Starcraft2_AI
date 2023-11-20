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
            
            for depo in self.structures(UnitTypeId.SUPPLYDEPOT).ready:
                self.do(depo(AbilityId.MORPH_SUPPLYDEPOT_LOWER))

            # Trénování SCV
            # Bot trénuje nová SCV, jestliže je jich méně než 24
            if self.can_afford(UnitTypeId.SCV) and self.supply_workers <= 24 and cc.is_idle:
                cc.train(UnitTypeId.SCV)
            
            # Zbylý SCV bot pošle těžit minerály nejblíže Command Center
            """ for scv in self.workers:
                
                for r in self.units(UnitTypeId.REFINERY):
                    if r.assigned_harvesters < r.ideal_harvesters :
                        scv.gather(r)
                while cc.assigned_harvesters < cc.ideal_harvesters:
                    scv.gather(self.mineral_field.closest_to(cc)) """
            if self.structures(UnitTypeId.REFINERY).ready.amount > 0:
                if cc.assigned_harvesters > cc.ideal_harvesters or self.idle_worker_count > 0:
                    for r in self.structures(UnitTypeId.REFINERY):
                        if r.assigned_harvesters < r.ideal_harvesters:
                            if self.idle_worker_count > 0 :
                                idle_SCVs=[x for x in self.units(UnitTypeId.SCV).idle]
                                for idle_SCV in idle_SCVs:
                                    idle_SCV.gather(r)
                                
                                """ for w in self.workers.idle:
                                    w.gather(r) """
                        if r.assigned_harvesters < r.ideal_harvesters :
                            #TODO ziskat harvestory co aktualne pracuju na mineraloch a jendoho z nich vzit
                            # HELP - udelat si napr 3 pole. jedno pole vsech harvestoru, druhe pole harvestoru na mineraloch a treti na gas. 
                            # PROBLEM - co udela harvestor po tom co se vytvori.. proste nekam automaticky jde.. je potreba ho odchytit
                            w = self.workers.closest_to(cc)
                            w.gather(r)

                

            # Postav Supply Depot, jestliže zbývá méně než 6 supply a je využito více než 13
            if self.supply_left < 6 and self.supply_used >= 14 and not self.already_pending(UnitTypeId.SUPPLYDEPOT):
                if self.can_afford(UnitTypeId.SUPPLYDEPOT):
                    # Budova bude postavena poblíž Command Center směrem ke středu mapy
                    # SCV pro stavbu bude vybráno automaticky viz dokumentace
                    await self.build(
                        UnitTypeId.SUPPLYDEPOT,
                        near=cc.position.towards(self.game_info.map_center, 8))
                    
            #Postav refinery na geysirech blizsich nez 25 od CC
            vaspenes = self.vespene_geyser.closer_than(20.0, cc)
            if vaspenes is not None:    
                for vaspene in vaspenes:
                    if not self.can_afford(UnitTypeId.REFINERY):
                        break
                    worker = self.select_build_worker(vaspene.position)
                    if worker is None:
                        break
                    if not self.units(UnitTypeId.REFINERY).closer_than(1.0, vaspene).exists:
                        await self.build(UnitTypeId.REFINERY, vaspene)

            # Stavba Barracks
            # Bot staví tak dlouho, dokud si může dovolit stavět Barracks a jejich počet je menší než 6
            if self.tech_requirement_progress(UnitTypeId.BARRACKS) == 1:
                # Je jich méně než 6 nebo se již nějaké nestaví
                if self.structures(UnitTypeId.BARRACKS).amount < 6:
                    if self.can_afford(UnitTypeId.BARRACKS) and not self.already_pending(UnitTypeId.BARRACKS):
                        await self.build(
                            UnitTypeId.BARRACKS,
                            near=cc.position.towards(self.game_info.map_center, 8))

            
            
            # Trénování jednotky Marine
            # Pouze, má-li bot postavené Barracks a může si jednotku dovolit
            """  if self.structures(UnitTypeId.BARRACKS) and self.can_afford(UnitTypeId.MARINE):
                # Každá budova Barracks trénuje v jeden čas pouze jednu jednotku (úspora zdrojů)
                for barrack in self.structures(UnitTypeId.BARRACKS).idle:
                    barrack.train(UnitTypeId.MARINE) """
                    
            if self.structures(UnitTypeId.BARRACKS) and self.can_afford(UnitTypeId.MARINE) and self.can_afford(UnitTypeId.MARAUDER):
                # Rozdělíme si barracky na dvě poloviny
                barracks_list = self.structures(UnitTypeId.BARRACKS).idle
                half_count = len(barracks_list) // 2
                if iteration % 2 == 1:
                    # První polovina trénuje Marine
                    for barrack in barracks_list[:half_count]:
                        barrack.train(UnitTypeId.MARINE)
                else:
                    # Druhá polovina trénuje Marauder
                    for barrack in barracks_list[half_count:]:
                        barrack.train(UnitTypeId.MARAUDER)

                

            # Útok s jednotkou Marine
            # Má-li bot více než 15 volných jednotek Marine, zaútočí na náhodnou nepřátelskou budovu nebo se přesune na jeho startovní pozici
            idle_marines = self.units(UnitTypeId.MARINE).idle
            idle_marauders = self.units(UnitTypeId.MARAUDER).idle
            if idle_marines.amount > 15:
                target = self.enemy_structures.random_or(
                    self.enemy_start_locations[0]).position
                for marine in idle_marines:
                    marine.attack(target)
                for marauder in idle_marauders:
                    marauder.attack(target)
                

run_game(maps.get("sc2-ai-cup-2022"), [
    Bot(Race.Terran, Bo_bot()),
    Computer(Race.Terran, Difficulty.Easy)
], realtime=False)
