import pandas as pd
from csv import reader
from time import sleep
from collections import Counter
from postgamestats import PostGameStats, init_Wrapper

def len_csv(csv_file, header=True):
    with open(csv_file) as f:
        len_csv = sum(1 for line in f)
    if header:
        len_csv -= 1
    return len_csv

csv_file = r"D:\Dokumente\Seafile\Seafile\Programming\_work\python\riot_v2\team_training_v2\input\input_scouting_team.csv"
with open(csv_file, "r") as read_obj:
    csv_reader = reader(read_obj)
    header = next(csv_reader)
    len_csv_ = len_csv(csv_file)

    player_roles_list = []
    bans_vs_list = []
    picks_list = []

    lol_watcher, champion_dict = init_Wrapper()

    print("Starting Task..\n")
    if header != None:
        for index, row in enumerate(csv_reader, 1):
            roles = ["Top", "Jgl", "Mid", "Adc", "Sup"]

            match_date = row[-1]
            match_id = row[1]
            team = row[2]
            check = row[4]
            print(f"Game {index}/{len_csv_} - {match_date}")

            if check != "1":
                game_stats = PostGameStats(match_id, lol_watcher, champion_dict)
                df_game = game_stats.dataframe

                if team == "BLUE":
                    df_team = df_game.iloc[:,:5]
                    picks = df_game.iloc[1,:5].values.tolist()
                    bans_vs = df_game.iloc[2,5:].values.tolist()
                elif team == "RED":
                    df_team = df_game.iloc[:,5:]
                    picks = df_game.iloc[1,5:].values.tolist()
                    bans_vs = df_game.iloc[2,:5].values.tolist()


                picks_list.extend(picks)
                bans_vs_list.extend(bans_vs)

                player_roles = [(player, indx) for indx, player in enumerate(df_team.loc["Summoner Name"])]
                
                for player_role in player_roles:
                    player = player_role[0]
                    role = player_role[1]
                    role = roles[role]

                    player_roles_list.append((player, role))

                sleep(8.5)



df_pr = pd.DataFrame(Counter(player_roles_list).most_common(),
                        columns=["Player, Role", "No. Games"])
df_pr["Playrate"] = round((df_pr["No. Games"] / len_csv_),2)

df_picks = pd.DataFrame(Counter(picks_list).most_common(),
                        columns=["Picked Champion", "No. Picks"])
df_picks["Pickrate"] = round((df_picks["No. Picks"] / len_csv_),2)

df_bans = pd.DataFrame(Counter(bans_vs_list).most_common(),
                        columns=["Banned Champion", "No. Bans"])
df_bans["Banrate"] = round((df_bans["No. Bans"] / len_csv_),2)


print("\n", df_pr)
print("\n", df_picks)
print("\n", df_bans)
