from postgamestats import init_Wrapper
import json

match_id = "EUW1_5836008004"

lol_watcher, champion_dict = init_Wrapper()
data_match, data_timeline = lol_watcher.match.by_id("europe", match_id), lol_watcher.match.timeline_by_match("europe", match_id)

path = r"D:\Dokumente\Seafile\Seafile\Programming\_work\python\riot_v2\team_training_v2\jsons\\"
file_match =  path + "MTCH_" + match_id + ".json"
file_timeline = path + "TMLN_" + match_id + ".json"

with open(file_match, "w") as out_file:
    json.dump(data_match, out_file, indent=4, sort_keys=True)

with open(file_timeline, "w") as out_file:
    json.dump(data_timeline, out_file, indent=4, sort_keys=True)
