class Proximity():
    def __init__(self, data, roleNums):
        self.data = data

        self.dict_pos = {  # Dict From Sorted Role Names List With Keys Sorted By List
            "blue":{
                "top" : [],
                "jgl" : [],
                "mid" : [],
                "adc" : [],
                "sup" : [],},
            "red":{
                "top" : [],
                "jgl" : [],
                "mid" : [],
                "adc" : [],
                "sup" : [],},}
        
        self.roleNums = roleNums
        self.roleNames = self.sortRoles(self.roleNums)

        self.getPositions()

    def getDistance(self, xy_cord_1:tuple, xy_cord_2:tuple):
        dist = ((xy_cord_2[0] - xy_cord_1[0])**2 + (xy_cord_2[1] - xy_cord_1[1])**2) ** 0.5

        return round(dist, 0)

    def getProximity(self, pos_laner:list, pos_jungler:list, range:int = 2000):
        i = 0
        positions = list(zip(pos_laner, pos_jungler))

        for pos in positions:
            dist = self.getDistance(pos[0], pos[1])
            if dist <= range:
                i += 1

        jgl_prx = i / len(positions)

        return jgl_prx

    def sortRoles(self, roleNums):
        roleNamesSorted = ["top", "jgl", "mid", "adc", "sup", "top", "jgl", "mid", "adc", "sup"]
        roleNames = []

        for k in roleNums:
            roleNames.append(roleNamesSorted[k])

        return roleNames

    def getPositions(self):
        for index, timeframe in enumerate(self.data["info"]["frames"], 1):
            if  3 <= index < 15:
                for role in range(1, 11):
                    if role < 6:
                        x = timeframe["participantFrames"][str(role)]["position"]["x"]
                        y = timeframe["participantFrames"][str(role)]["position"]["y"]
                        self.dict_pos["blue"][self.roleNames[role - 1]].append((x, y))
                    elif role > 5:
                        x = timeframe["participantFrames"][str(role)]["position"]["x"]
                        y = timeframe["participantFrames"][str(role)]["position"]["y"]
                        self.dict_pos["red"][self.roleNames[role - 1]].append((x, y))

    def calcProximity(self, lanestotrack, range):
        proximity_lst = []
        for key0 in self.dict_pos.keys():
            for key1 in self.dict_pos[key0].keys():
                if len(lanestotrack) > 1:
                    if key1 != lanestotrack[0] and key1 == lanestotrack[1]:
                        proximity_lst.append(round(self.getProximity(self.dict_pos[key0][key1], self.dict_pos[key0][lanestotrack[0]], range=range), 2))
                    else:
                        proximity_lst.append("/")
                else:
                    if key1 != lanestotrack[0]:
                        proximity_lst.append(round(self.getProximity(self.dict_pos[key0][key1], self.dict_pos[key0][lanestotrack[0]], range=range), 2))
                    else:
                        proximity_lst.append("/") 
        
        return proximity_lst

    def calcDiff(self, proximity_list):
        JPDiff = []
        for index, value in enumerate(proximity_list):
            if isinstance(value, float):
                if index < 5:
                    jpdiff = value - proximity_list[index + 5]
                    jpdiff = round(jpdiff, 2)
                elif index > 4:
                    jpdiff = value - proximity_list[index - 5]
                    jpdiff = round(jpdiff, 2)
            else:
                jpdiff = "/"
            JPDiff.append(jpdiff)

        return JPDiff


if __name__ == "__main__":
    from postgamestats import PostGameStats, init_Wrapper
    lol_watcher, champ_dict = init_Wrapper()

    match_id = "EUW1_5588524723"

    pgstats = PostGameStats(match_id, lol_watcher, champ_dict)
    roleNums = pgstats.game_roles

    data = pgstats.game_data_tmln
    prox = Proximity(data, roleNums)

    print(prox.calcProximity(("jgl",), range=2000))
