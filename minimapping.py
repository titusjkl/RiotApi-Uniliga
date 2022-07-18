import os, glob
import matplotlib.pyplot as plt
from PIL import Image
from postgamestats import init_Wrapper

lol_watcher, champion_dict = init_Wrapper()

class Minimapping():
    def __init__(self, url) -> None:
        self.url = url
        # self.data = lol_watcher.match.timeline_by_match("europe", self.url)

        # self.kills_blue, self.kills_red = self.MapKills()
        self.pos_blue, self.pos_red = self.MapHeatmap()

    def MakeGif(self, team):
        img = plt.imread(r"D:\Dokumente\Seafile\Seafile\Programming\_work\python\riot_v2\team_training_v2\sr_minimap.webp")
        _, ax = plt.subplots()
        ax.imshow(img, extent=[0,16000, 0,16000])
        ax.set_axis_off()
        for indx, coord in enumerate(self.pos_blue):
            ax.plot(coord["x"], coord["y"], ".", color="blue", mec="k", markersize=10)
            if indx % 5 == 0:
                plt.savefig(os.path.join(r"D:\Dokumente\Seafile\Seafile\Programming\_work\python\riot_v2\team_training_v2\mapping\gifs\frames", f"{indx:03d}_{self.url}_blue_heatmap.png"), bbox_inches='tight', pad_inches=0)
        plt.savefig(os.path.join(r"D:\Dokumente\Seafile\Seafile\Programming\_work\python\riot_v2\team_training_v2\mapping\heatmaps", f"{self.url}_blue_heatmap.png"), bbox_inches='tight', pad_inches=0)

        frames_folder = glob.glob(r"D:\Dokumente\Seafile\Seafile\Programming\_work\python\riot_v2\team_training_v2\mapping\gifs\frames\*.png")
        frames = [Image.open(image) for image in frames_folder
                if self.url and team in image]
        frame_one = frames[0]
        frame_one.save(fr"D:\Dokumente\Seafile\Seafile\Programming\_work\python\riot_v2\team_training_v2\mapping\gifs\{self.url}_heatmap.gif", format="GIF", append_images=frames,
               save_all=True, duration=250, loop=0)

        for file in frames_folder:
            if team in file:
                os.remove(file)

    def MapKills(self):
        kills_blue = []
        kills_red = []

        for timeframe in self.data["info"]["frames"]:
            for event in timeframe["events"]:
                if event["type"] == "CHAMPION_KILL":
                    try:
                        position = event["position"]
                        killer_id = event["killerId"]
                        if killer_id <= 5:
                            kills_blue.append(position)
                        else:
                            kills_red.append(position)
                    except KeyError:
                        pass
        
        img = plt.imread(r"D:\Dokumente\Seafile\Seafile\Programming\_work\python\riot_v2\team_training_v2\sr_minimap.webp")
        _, ax = plt.subplots()
        ax.imshow(img, extent=[0,16000, 0,16000])
        ax.set_axis_off()
        
        for pos in kills_blue:
            ax.plot(pos["x"], pos["y"], ".", color="blue", mec="k", markersize=10)
        for pos in kills_red:
            ax.plot(pos["x"], pos["y"], ".", color="red", mec="k", markersize=10)
                    
        plt.savefig(os.path.join(r"D:\Dokumente\Seafile\Seafile\Programming\_work\python\riot_v2\team_training_v2\mapping\kills", 
                    f"{self.url}_kills.png"), bbox_inches='tight', pad_inches=0)

        return kills_blue, kills_red

    def MapHeatmap(self):
        img = plt.imread(r"D:\Dokumente\Seafile\Seafile\Programming\_work\python\riot_v2\team_training_v2\sr_minimap.webp")

        if isinstance(self.url, str):
            pos_blue = []
            pos_red = []
            for timeframe in self.data["info"]["frames"]:
                for role in range(1,11): # blue team 
                    if role < 6:
                        pos = timeframe["participantFrames"][str(role)]["position"]
                        pos_blue.append(pos)
                    else:
                        pos = timeframe["participantFrames"][str(role)]["position"]
                        pos_red.append(pos)    

            _, ax = plt.subplots()
            ax.imshow(img, extent=[0,16000, 0,16000])
            ax.set_axis_off()
            for coord in pos_blue:
                ax.plot(coord["x"], coord["y"], ".", color="blue", mec="k", markersize=10)
            plt.savefig(os.path.join(r"D:\Dokumente\Seafile\Seafile\Programming\_work\python\riot_v2\team_training_v2\mapping\heatmaps", 
                        f"{self.url}_blue_heatmap.png"), bbox_inches='tight', pad_inches=0)

            _, ax = plt.subplots()
            ax.imshow(img, extent=[0,16000, 0,16000])
            ax.set_axis_off()
            for coord in pos_red:
                ax.plot(coord["x"], coord["y"], ".", color="red", mec="k", markersize=10)
            plt.savefig(os.path.join(r"D:\Dokumente\Seafile\Seafile\Programming\_work\python\riot_v2\team_training_v2\mapping\heatmaps", 
                        f"{self.url}_red_heatmap.png"), bbox_inches='tight', pad_inches=0)
            plt.clf()

        if isinstance(self.url, list):
            for indx, url in enumerate(self.url, start=1):
                data = lol_watcher.match.timeline_by_match("europe", url)
                pos_blue = []
                pos_red = []
                for timeframe in data["info"]["frames"]:
                    for role in range(1,11): # blue team 
                        if role < 6:
                            pos = timeframe["participantFrames"][str(role)]["position"]
                            pos_blue.append(pos)
                        else:
                            pos = timeframe["participantFrames"][str(role)]["position"]
                            pos_red.append(pos)    
                
                plt.subplots_adjust(left=None, bottom=None, right=None, top=1, wspace=0, hspace=None)

                plt_blue = plt.subplot(1, 2, 1)
                plt_blue.set_title(f"Game {indx}\nBlue Side")
                plt_blue.imshow(img, extent=[0,16000, 0,16000])
                plt_blue.set_axis_off()
                for coord in pos_blue:
                    plt_blue.plot(coord["x"], coord["y"], ".", color="blue", mec="k", markersize=10)

                plt_red = plt.subplot(1, 2, 2)
                plt_red.set_title(f"Game {indx}\nRed Side")
                plt_red.imshow(img, extent=[0,16000, 0,16000])
                plt_red.set_axis_off()
                for coord in pos_red:
                    plt_red.plot(coord["x"], coord["y"], ".", color="red", mec="k", markersize=10)
                
                plt.savefig(os.path.join(r"D:\Dokumente\Seafile\Seafile\Programming\_work\python\riot_v2\team_training_v2\mapping\heatmaps",
                        f"game{indx}_subplt_heatmap.png"),bbox_inches='tight', pad_inches=0, dpi=201.75*0.75)
                plt.clf()

        return pos_blue, pos_red

Minimapping(["EUW1_5594099926", "EUW1_5597050484"])


# with open(r"D:\Dokumente\Seafile\Seafile\Programming\__work\python_\riot_v2\team_training_v2\jsons\timeline_EUW1_5588524723.json") as f:
#     data = json.load(f)
#     with open(r"D:\Dokumente\Seafile\Seafile\Programming\__work\python_\riot_v2\team_training_v2\jsons\timeline_EUW1_5588524723.json", "w") as f_:
#         json.dump(data, f_, indent=4)

# with open(r"D:\Dokumente\Seafile\Seafile\Programming\__work\python_\riot_v2\team_training_v2\jsons\timeline_EUW1_5588524723.json", "r") as f:
#     timeline = json.load(f)

# pass_events = ["ITEM_DESTROYED", "SKILL_LEVEL_UP", "LEVEL_UP", "PAUSE_END", "ITEM_SOLD"]
# kills_blue = []
# kills_red = []

# for num_timeframe, timeframe in enumerate(timeline["info"]["frames"]):
#     for event in timeframe["events"]:
#         if event["type"] == "CHAMPION_KILL":
#             try:
#                 position = event["position"]
#                 killer_id = event["killerId"]
#                 if killer_id <= 5:
#                     kills_blue.append(position)
#                 else:
#                     kills_red.append(position)
#             except KeyError:
#                 pass

# img = plt.imread(r"D:\Dokumente\Seafile\Seafile\Programming\__work\python_\riot_v2\team_training_v2\sr_minimap.webp")
# fig, ax = plt.subplots()
# ax.imshow(img, extent=[0,16000, 0,16000])
# ax.set_axis_off()
# for pos in kills_blue:
#     ax.plot(pos["x"], pos["y"], ".", color="blue", mec="k", markersize=10)
# for pos in kills_red:
#     ax.plot(pos["x"], pos["y"], ".", color="red", mec="k", markersize=10)

# plt.savefig(r"D:\Dokumente\Seafile\Seafile\Programming\__work\python_\riot_v2\team_training_v2\mini.png", bbox_inches='tight', pad_inches=0)
# plt.show()
