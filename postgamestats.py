import config as cfg
import pandas as pd
import os, datetime, time
from riotwatcher import LolWatcher
from proximity import Proximity
from csv import reader
from time import sleep
import gspread
from df2gspread import df2gspread as df2gs
import gspread_formatting as gsf
from gspread_formatting import batch_updater


# with open(r"D:\Dokumente\Seafile\Seafile\Programming\_work\python\twitter_api\IsDiaBot\keys") as f:
#     lines = f.read().splitlines()

#     keys_dct = {}
#     new_key = {}
#     for line in lines:
#         new_key[line.split(" - ")[1]] = line.split(" - ")[0]
#         keys_dct.update(new_key)


def init_Wrapper(api_key=cfg.riot_api_key, region="euw1"):
    lol_watcher = LolWatcher(api_key)
    version = lol_watcher.data_dragon.versions_for_region(region)['n']['champion']
    champion_dict = lol_watcher.data_dragon.champions(version, full=True)["keys"]

    return lol_watcher, champion_dict

class PostGameStats():
    def __init__(self, url, lol_watcher, champion_dict):
        self.filepath = os.path.dirname(os.path.realpath(__file__))
        self.suffixes = ["_game", "_team", "_enemy",]
        self.paths = [os.path.join(self.filepath, "logs", f"by{suffix}") for suffix in self.suffixes]
        [os.makedirs(path, exist_ok=True) for path in self.paths]

        self.lol_watcher = lol_watcher
        self.champion_dict = champion_dict
        self.participant_num = range(0, 10)

        self.url = url
        self.game_id, self.match_region_v4, self.match_region_v5 = self.get_Match_Info()
        self.game_data_mtch, self.game_data_tmln = self.get_Game_Data()

        self.game_queue = self.get_Game_Queue()
        self.game_duration = self.get_Game_Duration()[0]
        self.game_date = self.get_Game_Duration()[1]
        self.game_duration_calcs = self.get_Game_Duration()[2]

        self.game_participants = self.get_Game_Participants()
        self.game_picked, self.game_roles, self.game_banned = self.get_Game_PickBan()
        self.game_winlose = self.get_Game_WinLoss()

        self.game_kda, self.game_kills, self.game_deaths, self.game_assists, self.game_kdaratio, self.game_kp = self.get_Game_KDA()
        self.game_firstblood = self.get_Game_FirstBlood()

        self.game_damage_dealt, self.game_damage_dealt_share, self.game_damage_per_minute = self.get_Game_Damage_Dealt()

        self.game_gold_earned, self.game_gold_earned_per_minute, self.game_gold_share, self.game_damage_per_gold, self.game_gold_per_damage = self.get_Game_Gold_Earned()

        self.game_damage_dealt_physical, self.game_damage_physical_share = self.get_Game_Damage_Dealt_Physical()
        self.game_damage_dealt_magical, self.game_damage_magical_share = self.get_Game_Damage_Dealt_Magical()
        self.game_damage_dealt_true, self.game_damage_true_share = self.get_Game_Damage_Dealt_True()

        self.game_damage_taken, self.game_damage_taken_per_minute = self.get_Game_Damage_Taken()
        self.game_healing_done, self.game_healing_done_per_minute= self.get_Game_Healing_Done()

        self.game_cs, self.game_cs_per_minute = self.get_Game_CS()
        self.game_neutral_cs, self.game_counter_jungle = self.get_Game_Jungle_Stats()

        self.game_wards_placed, self.game_cwards_placed, self.game_wards_killed = self.get_Game_Wards_Stats()
        self.game_vs, self.game_vs_per_minute = self.get_Game_VS()

        proximity_import = Proximity(self.game_data_tmln, self.game_roles)
        self.game_prox_jgl = proximity_import.calcProximity(("jgl",), range=2000)
        self.game_prox_jgl_diff = proximity_import.calcDiff(self.game_prox_jgl)
        self.game_prox_duo = proximity_import.calcProximity(("sup", "adc"), range=1000)

        self.index_list = ["Summoner Name", "Picked Champion", "Role", "Banned Champion", "Win / Loss",
                        "Kills / Deaths / Assists", "KDA Ratio", "Kill Participation [%]", "First Blood",
                        "CS", "CS per Minute", 
                        "Damage Dealt", "Damage Dealt Share [%]", "Physical Dmg Dealt", "Magic Dmg Dealt", "True Dmg Dealt",
                        "'Damage Dealt", "Damage per Minute", "Damage per Gold", "Gold per Damage",
                        "Damage Taken", "Healing Done",
                        "Gold Earned", "Gold Earned per Minute", "Gold Share [%]", 
                        "Neutral Minions Killed", "Counter Jungle Share", # 27
                        "Jungle Proximity", "Jungle Proximity Difference", "Duo Proximity", # 28 - 30
                        "Wards Placed", "Control Wards Placed", "Wards Killed", 
                        "Vision Score", "Vision Score per Minute",] # 35

        self.columns_list = ["Blue Player 1", "Blue Player 2", "Blue Player 3", "Blue Player 4", "Blue Player 5",
                            "Red Player 1",  "Red Player 2",  "Red Player 3",  "Red Player 4",  "Red Player 5",]

        self.full_list = self.create_Full_List()
        self.dataframe = self.fill_DataFrame()
    
        sleep(1)
    
    def get_Match_Info(self):
        dict_regions = {
                "BR1":"americas",
                "LA1":"americas",
                "LA2":"americas",
                "NA1":"americas",
                "JP1":"asia",
                "KR":"asia",
                "OC1":"asia",
                "RU":"asia",
                "EUN1":"europe",
                "EUW1":"europe",
                "TR1":"europe",}

        match_region_v4 = self.url.split("_")[0]
        game_id = self.url
        match_region_v5 = dict_regions[match_region_v4]

        return game_id, match_region_v4, match_region_v5

    def get_Game_Data(self):
        game_data_mtch = self.lol_watcher.match.by_id(self.match_region_v5, self.game_id)
        game_data_tmln = self.lol_watcher.match.timeline_by_match(self.match_region_v5, self.game_id)

        return game_data_mtch, game_data_tmln

    def get_Game_Queue(self):
        game_queue = self.game_data_mtch["info"]["gameType"].replace("_"," ").title()

        return game_queue

    def get_Game_Duration(self):
        if bool(self.game_data_mtch["info"]["gameEndTimestamp"]) == True:
            game_duration_calcs = round((self.game_data_mtch["info"]["gameDuration"] / 60), 2)
        else:
            game_duration_calcs = round(((self.game_data_mtch["info"]["gameDuration"] / 1000) / 60), 2)

        game_duration = time.strftime("%M:%S min", time.gmtime(game_duration_calcs*60))
        game_date = datetime.datetime.fromtimestamp(int(self.game_data_mtch["info"]["gameCreation"] / 1000)).strftime("%d.%m.%y, %H:%Mh")

        return game_duration, game_date, game_duration_calcs

    def get_Game_Participants(self):
        game_participants = [self.lol_watcher.summoner.by_puuid(self.match_region_v4, participant)["name"] for participant in self.game_data_mtch["metadata"]["participants"]]

        return game_participants

    def get_Game_WinLoss(self):
        game_winlose = ["Win" if self.game_data_mtch["info"]["participants"][participant]["win"] == True 
                        else "Loss" 
                        for participant in self.participant_num]

        return game_winlose

    def get_Champ_by_ID(self, id):
        champion = self.champion_dict[str(id)]

        return champion

    def get_Game_PickBan(self, BLUE=0, RED=1):
        game_picked = [self.game_data_mtch["info"]["participants"][participant]["championName"] for participant in self.participant_num]

        roles = range(0,10)
        game_roles = [roles[0] if self.game_data_mtch["info"]["participants"][participant]["teamPosition"] == "TOP" and participant < 5
                        else roles[1] if self.game_data_mtch["info"]["participants"][participant]["teamPosition"] == "JUNGLE" and participant < 5
                        else roles[2] if self.game_data_mtch["info"]["participants"][participant]["teamPosition"] == "MIDDLE" and participant < 5
                        else roles[3] if self.game_data_mtch["info"]["participants"][participant]["teamPosition"] == "BOTTOM" and participant < 5
                        else roles[4] if self.game_data_mtch["info"]["participants"][participant]["teamPosition"] == "UTILITY" and participant < 5
                        else roles[5] if self.game_data_mtch["info"]["participants"][participant]["teamPosition"] == "TOP" and participant >= 5
                        else roles[6] if self.game_data_mtch["info"]["participants"][participant]["teamPosition"] == "JUNGLE" and participant >= 5
                        else roles[7] if self.game_data_mtch["info"]["participants"][participant]["teamPosition"] == "MIDDLE" and participant >= 5
                        else roles[8] if self.game_data_mtch["info"]["participants"][participant]["teamPosition"] == "BOTTOM" and participant >= 5
                        else roles[9]
                        for participant in self.participant_num]

        blue_banned = [self.get_Champ_by_ID(self.game_data_mtch["info"]["teams"][BLUE]["bans"][ban]["championId"]) for ban in range(len(self.game_data_mtch["info"]["teams"][BLUE]["bans"]))]
        red_banned = [self.get_Champ_by_ID(self.game_data_mtch["info"]["teams"][RED]["bans"][ban]["championId"]) for ban in range(len(self.game_data_mtch["info"]["teams"][RED]["bans"]))]
        while len(blue_banned) < 5:
            blue_banned.append("NA")
        while len(red_banned) < 5:
            red_banned.append("NA")

        game_banned = blue_banned + red_banned

        return game_picked, game_roles, game_banned

    def get_Game_KDA(self):
        game_kills = [self.game_data_mtch["info"]["participants"][participant]["kills"] for participant in self.participant_num]
        game_deaths = [self.game_data_mtch["info"]["participants"][participant]["deaths"] for participant in self.participant_num]
        game_assists = [self.game_data_mtch["info"]["participants"][participant]["assists"] for participant in self.participant_num]
        game_kda = [f'''{self.game_data_mtch["info"]["participants"][participant]["kills"]} / {self.game_data_mtch["info"]["participants"][participant]["deaths"]} / {self.game_data_mtch["info"]["participants"][participant]["assists"]}'''
                        for participant in self.participant_num]
        
        game_kdaratio = [round(((game_kills[participant] + game_assists[participant]) / game_deaths[participant]), 1) if game_deaths[participant] != 0 
                            else (game_kills[participant] + game_assists[participant]) 
                            for participant in self.participant_num]

        game_kp = [round((game_kills[participant] + game_assists[participant]) / sum(game_kills[0:5]), 2) if participant < 5 
                    else round((game_kills[participant] + game_assists[participant]) / sum(game_kills[5:10]), 2) 
                    for participant in self.participant_num]

        return game_kda, game_kills, game_deaths, game_assists, game_kdaratio, game_kp

    def get_Game_FirstBlood(self):
        game_firstblood = ["First Blood" if self.game_data_mtch["info"]["participants"][participant]["firstBloodKill"] == True 
                            else "Assist" if self.game_data_mtch["info"]["participants"][participant]["firstBloodAssist"] == True 
                            else "False" 
                            for participant in self.participant_num]

        return game_firstblood

    def get_Game_Damage_Dealt(self):
        game_damage_dealt = [self.game_data_mtch["info"]["participants"][participant]["totalDamageDealtToChampions"] for participant in self.participant_num]
        game_damage_dealt_share = [round((game_damage_dealt[participant] / sum(game_damage_dealt[0:5])), 2) if participant < 5 
                                    else round((game_damage_dealt[participant] / sum(game_damage_dealt[5:10])), 2) 
                                    for participant in self.participant_num]
        game_damage_per_minute = [round(game_damage_dealt[participant] / self.game_duration_calcs, 1) for participant in self.participant_num]

        return game_damage_dealt, game_damage_dealt_share, game_damage_per_minute

    def get_Game_Gold_Earned(self):
        game_gold_earned = [self.game_data_mtch["info"]["participants"][participant]["goldEarned"] for participant in self.participant_num]
        game_gold_per_minute = [round(game_gold_earned[participant] / self.game_duration_calcs, 2) for participant in self.participant_num]
        game_gold_share = [round((game_gold_earned[participant] / sum(game_gold_earned[0:5])), 2) if participant < 5 
                            else round((game_gold_earned[participant] / sum(game_gold_earned[5:10])), 2) 
                            for participant in self.participant_num]

        game_damage_per_gold = [round(self.game_damage_dealt[participant] / game_gold_earned[participant], 2) for participant in self.participant_num]
        game_gold_per_damage = [round(game_gold_earned[participant] / self.game_damage_dealt[participant], 2) for participant in self.participant_num]

        return game_gold_earned, game_gold_per_minute, game_gold_share, game_damage_per_gold, game_gold_per_damage

    def get_Game_Damage_Dealt_Physical(self):
        game_damage_dealt_physical = [self.game_data_mtch["info"]["participants"][participant]["physicalDamageDealtToChampions"] for participant in self.participant_num]
        game_damage_dealt_physical_share = [round((game_damage_dealt_physical[participant] / self.game_damage_dealt[participant]), 2) for participant in self.participant_num]

        return game_damage_dealt_physical, game_damage_dealt_physical_share

    def get_Game_Damage_Dealt_Magical(self):
        game_damage_dealt_magical = [self.game_data_mtch["info"]["participants"][participant]["magicDamageDealtToChampions"] for participant in self.participant_num]
        game_damage_dealt_magical_share = [round((game_damage_dealt_magical[participant] / self.game_damage_dealt[participant]), 2) for participant in self.participant_num]

        return game_damage_dealt_magical, game_damage_dealt_magical_share

    def get_Game_Damage_Dealt_True(self):
        game_damage_dealt_true = [self.game_data_mtch["info"]["participants"][participant]["trueDamageDealtToChampions"] for participant in self.participant_num]
        game_damage_dealt_true_share = [round((game_damage_dealt_true[participant] / self.game_damage_dealt[participant]), 2) for participant in self.participant_num]

        return game_damage_dealt_true, game_damage_dealt_true_share

    def get_Game_Damage_Taken(self):
        game_damage_taken = [self.game_data_mtch["info"]["participants"][participant]["totalDamageTaken"] for participant in self.participant_num]
        game_damage_taken_per_minute = [round((game_damage_taken[participant] / self.game_duration_calcs),1) for participant in self.participant_num]

        return game_damage_taken, game_damage_taken_per_minute

    def get_Game_Healing_Done(self):
        game_healing_done = [(self.game_data_mtch["info"]["participants"][participant]["totalHeal"] + self.game_data_mtch["info"]["participants"][participant]["totalHealsOnTeammates"]) 
                                for participant in self.participant_num]
        game_healing_done_per_minute = [round((game_healing_done[participant] / self.game_duration_calcs),1) for participant in self.participant_num]

        return game_healing_done, game_healing_done_per_minute

    def get_Game_CS(self):
        game_cs = [self.game_data_mtch["info"]["participants"][participant]["totalMinionsKilled"] + self.game_data_mtch["info"]["participants"][participant]["neutralMinionsKilled"] 
                    for participant in self.participant_num]
        game_cs_per_minute = [round((game_cs[participant] / self.game_duration_calcs), 1) for participant in self.participant_num]

        return game_cs, game_cs_per_minute

    def get_Game_Jungle_Stats(self):
        game_neutral_cs = [self.game_data_mtch["info"]["participants"][participant]["neutralMinionsKilled"] for participant in self.participant_num]
        game_counter_jungle = ["Deprecated"] * 10

        return game_neutral_cs, game_counter_jungle

    def get_Game_Wards_Stats(self):
        game_wards_placed = [self.game_data_mtch["info"]["participants"][participant]["wardsPlaced"] for participant in self.participant_num]
        game_cwards_placed = [self.game_data_mtch["info"]["participants"][participant]["detectorWardsPlaced"] for participant in self.participant_num]
        game_wards_killed = [self.game_data_mtch["info"]["participants"][participant]["wardsKilled"] for participant in self.participant_num]

        return game_wards_placed, game_cwards_placed, game_wards_killed

    def get_Game_VS(self):
        game_vs = [self.game_data_mtch["info"]["participants"][participant]["visionScore"] for participant in self.participant_num]
        game_vs_per_minute = [round((game_vs[participant] / self.game_duration_calcs), 1) for participant in self.participant_num]

        return game_vs, game_vs_per_minute

    def create_Full_List(self):
        stats = [self.game_participants, self.game_picked, self.game_roles, self.game_banned, self.game_winlose, 
                self.game_kda, self.game_kdaratio, self.game_kp, self.game_firstblood,
                self.game_cs, self.game_cs_per_minute,
                self.game_damage_dealt, self.game_damage_dealt_share, self.game_damage_dealt_physical, self.game_damage_dealt_magical, self.game_damage_dealt_true,
                self.game_damage_dealt, self.game_damage_per_minute, self.game_damage_per_gold, self.game_gold_per_damage,
                self.game_damage_taken, self.game_healing_done,
                self.game_gold_earned, self.game_gold_earned_per_minute, self.game_gold_share,
                self.game_neutral_cs, self.game_counter_jungle, self.game_prox_jgl, self.game_prox_jgl_diff, self.game_prox_duo,
                self.game_wards_placed, self.game_cwards_placed, self.game_wards_killed, self.game_vs, self.game_vs_per_minute,]
        full_list = [stat for stat in stats]

        return full_list

    def fill_DataFrame(self):
        print("\tFilling dataframe..")
        dataframe = pd.DataFrame(self.full_list,
                                index=self.index_list,
                                columns=self.columns_list)

        list_sort_1 = self.index_list[0:27]
        df_sort_1 = dataframe.loc[list_sort_1]
        df_sort_1.sort_values(by="Role", axis=1, inplace=True)
        df_sort_1.drop("Role", inplace=True)

        list_sort_2 = ["Role"]
        list_sort_2.extend(self.index_list[30:35])
        df_sort_2 = dataframe.loc[list_sort_2]
        df_sort_2.sort_values(by="Role", axis=1, inplace=True)
        df_sort_2.drop("Role", inplace=True)

        temp_col_names = []
        for roleNum in self.game_roles:
            temp_col_names.append(self.columns_list[roleNum])
        list_prox = self.index_list[27:30]

        df_prox = dataframe.loc[list_prox]
        df_prox.columns = temp_col_names

        finished_df = df_sort_1.append([df_prox, df_sort_2])
        finished_df.columns = self.columns_list

        return finished_df

    def write_to_CSV(self, dataframe, filename, fileending):
        filename = filename.lower()
        filename_suffix = ".csv"

        if "_full" in fileending:
            path = os.path.join(self.paths[0], filename+"_full"+filename_suffix)
        elif "_team" in fileending:
            path = os.path.join(self.paths[1], filename+"_team"+filename_suffix)
        elif "_enemy" in fileending:
            path = os.path.join(self.paths[2], filename+"_enemy"+filename_suffix)

        dataframe.to_csv(path, encoding="utf-8")

class SpreadsheetFormatting():
    def __init__(self, match_name, spreadsheet_key, service_account_path):
        self.match_name = match_name

        self.spreadsheet_key = spreadsheet_key
        self.service_account_path = service_account_path
        self.gc = gspread.service_account(self.service_account_path)

        self.spreadsheet = self.gc.open_by_key(self.spreadsheet_key)
        
        try:
            self.spreadsheet.add_worksheet(self.match_name, rows=40, cols=16)
        except gspread.exceptions.APIError:
            pass
        self.worksheet = self.spreadsheet.worksheet(self.match_name)

    @staticmethod
    def to_RGBSCALE(to_scale):
        scale = to_scale / 255

        return scale

    def set_Worksheet_Format(self):
        formatting = {"fmt_centered": gsf.cellFormat(horizontalAlignment="CENTER"),
            "fmt_left": gsf.cellFormat(horizontalAlignment="LEFT"),
            "fmt_bold": gsf.cellFormat(textFormat=gsf.textFormat(bold=True),),
            "fmt_cursive": gsf.cellFormat(textFormat=gsf.textFormat(italic=True),),
            "fmt_blueteam": gsf.cellFormat(backgroundColor=gsf.color(self.to_RGBSCALE(109), self.to_RGBSCALE(158), self.to_RGBSCALE(235))),
            "fmt_redteam": gsf.cellFormat(backgroundColor=gsf.color(self.to_RGBSCALE(224), self.to_RGBSCALE(102), self.to_RGBSCALE(102))),
            "fmt_a_basics": gsf.cellFormat(backgroundColor=gsf.color(self.to_RGBSCALE(162), self.to_RGBSCALE(196), self.to_RGBSCALE(201))),
            "fmt_bk_basics": gsf.cellFormat(backgroundColor=gsf.color(self.to_RGBSCALE(208), self.to_RGBSCALE(224), self.to_RGBSCALE(227))),
            "fmt_a_kda": gsf.cellFormat(backgroundColor=gsf.color(self.to_RGBSCALE(221), self.to_RGBSCALE(126), self.to_RGBSCALE(107))),
            "fmt_bk_kda": gsf.cellFormat(backgroundColor=gsf.color(self.to_RGBSCALE(230), self.to_RGBSCALE(184), self.to_RGBSCALE(175))),
            "fmt_a_dmg": gsf.cellFormat(backgroundColor=gsf.color(self.to_RGBSCALE(246), self.to_RGBSCALE(178), self.to_RGBSCALE(107))),
            "fmt_bk_dmg": gsf.cellFormat(backgroundColor=gsf.color(self.to_RGBSCALE(249), self.to_RGBSCALE(203), self.to_RGBSCALE(156))),
            "fmt_a_dmgdealt": gsf.cellFormat(backgroundColor=gsf.color(self.to_RGBSCALE(162), self.to_RGBSCALE(160), self.to_RGBSCALE(216))),
            "fmt_bk_dmgdealt": gsf.cellFormat(backgroundColor=gsf.color(self.to_RGBSCALE(217), self.to_RGBSCALE(210), self.to_RGBSCALE(233))),
            "fmt_a_dmgtaken": gsf.cellFormat(backgroundColor=gsf.color(self.to_RGBSCALE(213), self.to_RGBSCALE(166), self.to_RGBSCALE(189))),
            "fmt_bk_dmgtaken": gsf.cellFormat(backgroundColor=gsf.color(self.to_RGBSCALE(234), self.to_RGBSCALE(209), self.to_RGBSCALE(220))),
            "fmt_a_cs": gsf.cellFormat(backgroundColor=gsf.color(self.to_RGBSCALE(255), self.to_RGBSCALE(229), self.to_RGBSCALE(153))),
            "fmt_bk_cs": gsf.cellFormat(backgroundColor=gsf.color(self.to_RGBSCALE(255), self.to_RGBSCALE(242), self.to_RGBSCALE(204))),
            "fmt_a_gold": gsf.cellFormat(backgroundColor=gsf.color(self.to_RGBSCALE(159), self.to_RGBSCALE(197), self.to_RGBSCALE(232))),
            "fmt_bk_gold": gsf.cellFormat(backgroundColor=gsf.color(self.to_RGBSCALE(207), self.to_RGBSCALE(226), self.to_RGBSCALE(243))),
            "fmt_a_jgl": gsf.cellFormat(backgroundColor=gsf.color(self.to_RGBSCALE(221), self.to_RGBSCALE(126), self.to_RGBSCALE(107))),
            "fmt_bk_jgl": gsf.cellFormat(backgroundColor=gsf.color(self.to_RGBSCALE(230), self.to_RGBSCALE(184), self.to_RGBSCALE(175))),
            "fmt_a_prox": gsf.cellFormat(backgroundColor=gsf.color(self.to_RGBSCALE(246), self.to_RGBSCALE(178), self.to_RGBSCALE(107))),
            "fmt_bk_prox": gsf.cellFormat(backgroundColor=gsf.color(self.to_RGBSCALE(249), self.to_RGBSCALE(203), self.to_RGBSCALE(156))),
            "fmt_a_vision": gsf.cellFormat(backgroundColor=gsf.color(self.to_RGBSCALE(182), self.to_RGBSCALE(215), self.to_RGBSCALE(168))),
            "fmt_bk_vision": gsf.cellFormat(backgroundColor=gsf.color(self.to_RGBSCALE(217), self.to_RGBSCALE(234), self.to_RGBSCALE(211))),
            }

        with batch_updater(self.worksheet.spreadsheet) as batch:
            print(f"\tFormatting Worksheet '{self.match_name}'..")

            batch.set_frozen(self.worksheet, rows=1)
            batch.set_column_widths(self.worksheet, [("A", 175), ("B:K", 115), ("M", 160)])
            batch.format_cell_ranges(self.worksheet, [
                ("A", formatting["fmt_left"]), ("B:K", formatting["fmt_centered"]), ("A1", formatting["fmt_centered"]),
                ("B1:F1", formatting["fmt_blueteam"]), ("G1:K1", formatting["fmt_redteam"]),
                ("A2:A5", formatting["fmt_a_basics"]), ("B2:K5", formatting["fmt_bk_basics"]), ("B3:K3", formatting["fmt_bold"]), ("B4:K4", formatting["fmt_cursive"]),
                ("A6:A9", formatting["fmt_a_kda"]), ("B6:K9", formatting["fmt_bk_kda"]), 
                ("A10:A11", formatting["fmt_a_dmg"]), ("B10:K11", formatting["fmt_bk_dmg"]), 
                ("A12:A16", formatting["fmt_a_dmgdealt"]), ("B12:K16", formatting["fmt_bk_dmgdealt"]), 
                ("A17:A20", formatting["fmt_a_dmgtaken"]), ("B17:K20", formatting["fmt_bk_dmgtaken"]), 
                ("A21:A22", formatting["fmt_a_cs"]), ("B21:K22", formatting["fmt_bk_cs"]), 
                ("A23:A25", formatting["fmt_a_gold"]), ("B23:K25", formatting["fmt_bk_gold"]), 
                ("A26:A27", formatting["fmt_a_jgl"]), ("B26:K27", formatting["fmt_bk_jgl"]), ("B27:K27", formatting["fmt_cursive"]),
                ("A28:A30", formatting["fmt_a_prox"]), ("B28:K30", formatting["fmt_bk_prox"]),  
                ("A31:A35", formatting["fmt_a_vision"]), ("B31:K35", formatting["fmt_bk_vision"]),])

def commit_to_Spreadsheet(input_path, spreadsheet_key, service_account_path, UPLOAD=True):
    with open(input_path, "r") as read_obj:
        csv_reader = reader(read_obj)
        header = next(csv_reader)
        print("Starting Task..\n")

        lol_watcher, champion_dict = init_Wrapper()

        if header != None:
            for row in csv_reader:
                match_name = row[0]
                match_url = row[1]
                team = row[2]
                check = row[3]

                print(f"{match_name}")
                if check != "1":
                    game_stats = PostGameStats(match_url, lol_watcher, champion_dict)
                    # game_queue = game_stats.game_queue
                    game_duration = game_stats.game_duration #time.strftime("%M:%S min", time.gmtime(game_stats.game_duration*60))
                    game_date = game_stats.game_date
                    df_game = game_stats.dataframe

                    # if team == "BLUE":
                    #     df_team = df_game.iloc[:,:5]
                    #     df_enemy = df_game.iloc[:,5:]
                    # elif team == "RED":
                    #     df_team = df_game.iloc[:,5:]
                    #     df_enemy = df_game.iloc[:,:5]

                    game_stats.write_to_CSV(df_game, match_name, "by_full")
                    # game_stats.write_to_CSV(df_team, match_name, "by_team")
                    # game_stats.write_to_CSV(df_enemy, match_name, "by_enemy")

                    if UPLOAD:
                        spreadsheet_formatting_ = SpreadsheetFormatting(match_name, spreadsheet_key=spreadsheet_key, service_account_path=service_account_path)

                        print("\tUploading Statistics..")
                        df2gs.upload(df_game, spreadsheet_formatting_.spreadsheet_key, match_name, credentials=cfg.credentials(spreadsheet_formatting_.service_account_path), 
                                    col_names = False, row_names= True, start_cell = "A2",)

                        spreadsheet_formatting_.worksheet.batch_update([{
                            "range": "A1",
                            "values": [[f"{game_duration} - {game_date}"]]
                            },{
                            "range": "B1:K1",
                            "values": [game_stats.columns_list],
                            },{
                            "range": "M2",
                            "values": [[f"{match_name}"]],
                            },{
                            "range": "M3",
                            "values": [[game_stats.game_id]],
                            },{
                            "range": "M5",
                            "values": [[f"Notes: "]],
                            },])
                        sleep(1)
                        spreadsheet_formatting_.set_Worksheet_Format()
                        print(f"\tUpload Finished!\n")
                    else:
                        print("\tSkipping Upload..\n")
                else:
                    print(f"\tSkipping Game..\n")   

            print("Task Finshed!\n")
            sleep(1.75)


if __name__ == "__main__":   
    uploader = True
    commit_to_Spreadsheet(UPLOAD=uploader, spreadsheet_key = cfg.google_sheets["SPREADSHEET_KEY_GAMESTATS"], 
                            input_path = r"D:\Dokumente\Seafile\Seafile\Programming\_work\python\riot_v2\team_training_v2\input\input_own_games.csv", 
                            service_account_path = r"D:\Dokumente\Seafile\Seafile\Programming\_work\python\riot_v2\team_training_v2\service_account.json")

    # commit_to_Spreadsheet(UPLOAD=uploader, spreadsheet_key = cfg.google_sheets["SPREADSHEET_KEY_SCOUTING"], 
    #                         input_path = r"D:\Dokumente\Seafile\Seafile\Programming\_work\python\riot_v2\team_training_v2\input\input_scouting.csv", 
    #                         service_account_path = r"D:\Dokumente\Seafile\Seafile\Programming\_work\python\riot_v2\team_training_v2\service_account.json")
