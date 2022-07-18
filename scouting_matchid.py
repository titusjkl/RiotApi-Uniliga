import config as cfg
from riotwatcher import LolWatcher
from datetime import datetime
from time import sleep
import numpy as np

lol_watcher = LolWatcher(cfg.riot_api_key)

def KeyfromValue(dict, value):
    found_key = [k for k, v in dict.items() if v == value]
    return found_key[0]

own_team = "CVBendixx,GregorOmp,VININElluuk,Hovercraft,Trifftníx,StrikerGL,Sekundus"
def getMatches(team_members=own_team, start_time=None, queue=None, matchType="tourney"):
    if not isinstance(team_members, list):
        team_members = team_members.split(",")

    team_summoners = [lol_watcher.summoner.by_name("euw1", summoner_name) for summoner_name in team_members]
    team_puuids = [summoner["puuid"] for summoner in team_summoners]
    team_ids = [summoner["id"] for summoner in team_summoners]

    time_unix = int(datetime.strptime(start_time, "%d.%m.%y").timestamp())
    time_string = datetime.fromtimestamp(time_unix).strftime('%d.%m.%y')
    
    print(f"Fetching Matches Of Match Type '{matchType.title()}' For {len(team_members)} Players, Starting From {time_string}\n")

    matches_set = set()
    for puuid in team_puuids:
        match_list = lol_watcher.match.matchlist_by_puuid("europe", puuid, count=100, queue=queue, type=matchType, start_time=time_unix)
        matches_set.update(match_list)
        sleep(0.5)
        
    return sorted(matches_set), team_puuids, team_ids

def getProfiles(team_ids,region = "euw1"):
    elo_dict = {
        "ur":0,
        "ir4":1,
        "ir3":2,
        "ir2":3,
        "ir1":4,
        "br4":5,
        "br3":6,
        "br2":7,
        "br1":8,
        "si4":9,
        "si3":10,
        "si2":11,
        "si1":12,
        "go4":13,
        "go3":14,
        "go2":15,
        "go1":16,
        "pl4":17,
        "pl3":18,
        "pl2":19,
        "pl1":20,
        "di4":21,
        "di3":22,
        "di2":23,
        "di1":24,
        "ma1":25,
        "gr1":26,
        "ch1":27,
    }

    team_league = [lol_watcher.league.by_summoner(region, team_id) for team_id in team_ids]
    team_league = dict(zip(team_ids,team_league))

    team_elos = []
    for team_id in team_ids:
        if len(team_league[team_id]) > 0:
            for summoner_league in team_league[team_id]:
                if summoner_league["queueType"] == "RANKED_SOLO_5x5":
                    tier = summoner_league["tier"][:2]
                    rank = len(summoner_league["rank"])
                    elo = f"{tier.lower()}{rank}"
                    team_elos.append(elo)
                else:
                    team_elos.append("ur")


    elos_num = [elo_dict[elo_str] for elo_str in team_elos]
    elos_array = np.array(elos_num)

    avg_elo_num_z = round(np.mean(elos_array))
    avg_elo_str_z = KeyfromValue(elo_dict, avg_elo_num_z).title()

    avg_elo_num_nz = round(elos_array[np.nonzero(elos_array)].mean())
    avg_elo_str_nz = KeyfromValue(elo_dict, avg_elo_num_nz).title()

    ur_players = elos_num.count(0)
    min_elo = KeyfromValue(elo_dict, elos_array[np.nonzero(elos_array)].min()).title()
    max_elo = KeyfromValue(elo_dict, elos_array[np.nonzero(elos_array)].max()).title()

    print(f"""Average Team-Elo Across {len(elos_num)} Players: {avg_elo_str_z}
         Without Unranked Players: {avg_elo_str_nz}
Max Elo: {max_elo}
Min Elo: {min_elo}
Unranked Players: {ur_players}/{len(elos_num)}""")

def getInfos(matches, team_puuids, players_treshhold=5):
    csv_results = []
    wongames = 0

    print(f"\n{len(matches)} Matches Found\n")

    for index, match in enumerate(matches, 1):
        match_data = lol_watcher.match.by_id("europe", match)

        game_puuids = match_data["metadata"]["participants"]

        timestamp = int(match_data["info"]["gameCreation"] / 1000)
        ddmmyyhhmm = datetime.fromtimestamp(timestamp).strftime('%d.%m.%y - %H:%M')
        ddmmyy = datetime.fromtimestamp(timestamp).strftime('%d.%m.%y')

        if len(set(team_puuids) & set(game_puuids)) >= players_treshhold:
            if len(set(team_puuids) & set(game_puuids[0:5])) >= players_treshhold:
                team = "BLUE"
            elif len(set(team_puuids) & set(game_puuids[5:10])) >= players_treshhold:
                team = "RED"
        
            print(index,"/", len(matches), "-", len(set(team_puuids) & set(game_puuids)), "-", ddmmyy)

            if team == "BLUE" and match_data["info"]["teams"][0]["win"]:
                win = True
                wongames += 1
            elif team == "RED" and match_data["info"]["teams"][1]["win"]:
                win = True
                wongames += 1
            else:
                win = False

            csv_line = f",{match},{team},{win},0,{ddmmyyhhmm}"
            csv_results.append((csv_line,timestamp))

        sleep(0.33)

    csv_results = sorted(csv_results, key=lambda x:x[1])
    csv_results = [result[0] for result in csv_results]

    print(f"\n{len(csv_results)}/{len(matches)} Matches Played As A Team")
    print(f"{round(wongames/len(matches)*100,2)}% Winrate\n")

    print(*csv_results, sep="\n")

    return csv_results


summoner_names = "IINoobKillerII,PaulanerWeißbier,321nomis,FlingtoWin,CptHero,Shyll,Kekskrümel"
tourney_set, puuids, ids = getMatches(summoner_names, start_time="26.10.21")

tourney_set, puuids, ids = getMatches(start_time="01.04.22")

getProfiles(ids)

csv_results = getInfos(tourney_set, puuids)
