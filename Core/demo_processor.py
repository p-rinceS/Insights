from traceback import print_exc
import pandas as pd
from demoparser2 import DemoParser
import os
import shutil
import uuid
import random
from dotenv import find_dotenv, load_dotenv

dotenv_path = find_dotenv()
load_dotenv(dotenv_path)

def clear_voices_directory():
    voices_dir = "../assets/output/voices"
    if os.path.exists(voices_dir):
        for item in os.listdir(voices_dir):
            item_path = os.path.join(voices_dir, item)
            if os.path.isfile(item_path):
                os.remove(item_path)
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)
    else:
        print(f"Demo folder {voices_dir} does not exist.")


def process_demo(demo_path):
    try:
        parser = DemoParser(demo_path)
    except FileNotFoundError:
        raise FileNotFoundError(f"Demo file not found: {demo_path}")
    return parser

def extract_team_data(players, team_number):
    return players[players['team_number'] == team_number].apply(
        lambda row: {"name": row['name'], "steamid": row['steamid']}, axis=1
    ).tolist()

class DemoProcessor:
    def __init__(self, demo_path):
        self.demo_path = demo_path
        self.demo_id = os.path.splitext(os.path.basename(demo_path))[0]

    def get_player_teams(self):
        try:
            parser = process_demo(self.demo_path)
            players = parser.parse_player_info()
            teams = players['team_number'].unique()
            team1 = extract_team_data(players, teams[0])
            team2 = extract_team_data(players, teams[1])
            return team1, team2
        except Exception as e:
            print(f"An error occurred while getting player teams: {e}")
            return [], []

    def get_name_from_steam_id(self, steam_id):
        try:
            steam_id = int(steam_id)  # Ensure steam_id is always an integer
        except ValueError:
            print(f"Invalid Steam ID: {steam_id}. Steam ID must be an integer.")
        try:
            parser = process_demo(self.demo_path)
            players = parser.parse_player_info()
            player_row = players.loc[players['steamid'] == steam_id]
            return player_row['name'].values[0] if not player_row.empty else "Unknown Player"
        except Exception as e:
            print(f"An error occurred while retrieving player name: {e}")
            return "Unknown Player"

    def get_round_end_ticks(self):
        try:
            parser = process_demo(self.demo_path)
            round_end_ticks = parser.parse_event("round_end")["tick"]
            # Return a list of round end ticks
            tick_list = list(round_end_ticks)
            print(f"Round end ticks: {tick_list}")
            return tick_list
        except Exception as e:
            print(f"An error occurred while getting round end ticks: {e}")
            return []
        
    def get_round_start_ticks(self):
        try:
            parser = process_demo(self.demo_path)
            print(f"game events: {parser.list_game_events()}")
            round_start_ticks = parser.parse_event("round_start")["tick"]
            # subtract 100 from every item in round_start_ticks
            # Filter out ticks that are not at least 500 greater than the previous tick
            filtered_ticks = []
            for tick in round_start_ticks:
                if not filtered_ticks or tick - filtered_ticks[-1] > 500:
                    filtered_ticks.append(tick)
            # Return a list of round end ticks
            tick_list = filtered_ticks
            print(f"Round start ticks: {tick_list}")
            return tick_list
        except Exception as e:
            print(f"An error occurred while getting round start ticks: {e}")
            return []

    def process_voices_by_team(self):
        try:
            parser = process_demo(self.demo_path)
            streamed_bytes = parser.parse_voice()
            team1, team2 = self.get_player_teams()
            team1_steam_ids = [player['steamid'] for player in team1]
            team2_steam_ids = [player['steamid'] for player in team2]
            # Eventually store this in AWS S3 or similar storage, but for now, we will output to files
            voices_dir = "../assets/output/voices"
            demo_folder = os.path.join(voices_dir, str(self.demo_id))
            os.makedirs(demo_folder, exist_ok=True)
            # Process the streamed bytes and write them to files based on team membership
            for steam_id, raw_bytes in streamed_bytes.items():
                # if steam id is in team1, output the file in "../assets/output/voices/team1/steam_id.wav"
                if int(steam_id) in team1_steam_ids:
                    with open(f"../assets/output/voices/{self.demo_id}/T1-{self.get_name_from_steam_id(int(steam_id))}.wav", "wb") as f:
                        f.write(raw_bytes)
                elif int(steam_id) in team2_steam_ids:
                    with open(f"../assets/output/voices/{self.demo_id}/T2-{self.get_name_from_steam_id(int(steam_id))}.wav", "wb") as f:
                        f.write(raw_bytes)
        except Exception as e:
            print(f"An error occurred while processing voices by team: {e}")

    def get_demo_id(self):
        return self.demo_id
    
    def set_demo_id(self, demo_id):
        self.demo_id = demo_id

    def get_start_time(self):
        try:
            parser = process_demo(self.demo_path)
            return parser.parse_event("round_start").get("time", None)
        except Exception as e:
            print(f"An error occurred while getting start time: {e}")
            return None


    def get_game_leaderboard_every_round(self, round):
        try:
            parser = process_demo(self.demo_path)
            round_end_ticks = self.get_round_end_ticks()
            print(f"Game end tick: {round_end_ticks[round]}")
            wanted_fields = ["kills_total", "deaths_total","assists_total",  "mvps"]
            df = parser.parse_ticks(wanted_fields, ticks=[round_end_ticks[round]])
            print(df)
        except Exception as e:
            print(f"An error occurred while getting player positions at round {round + 1}: {e}")
            return None
        
    # Return a list of all ticks between the start and end of a specified round
    def get_ticks_between_rounds(self, round):
        try:
            round_start_ticks = self.get_round_start_ticks()
            print(len(round_start_ticks))
            round_end_ticks = self.get_round_end_ticks()
            print(len(round_end_ticks))
            if (len(round_start_ticks) != len(round_end_ticks)):
                raise ValueError("Round start and end ticks lists must be of the same length.")
            
            # Get Round_Start_Ticks[round] and Round_End_Ticks[round]
            # Return every tick between these two ticks
            if round < 0 or round >= len(round_start_ticks) or round >= len(round_end_ticks):
                raise IndexError("Round index out of range.")
            start_tick = round_start_ticks[round]
            end_tick = round_end_ticks[round]
            if start_tick is None or end_tick is None:
                raise ValueError("Start or end tick is None.")
            if start_tick >= end_tick:
                raise ValueError("Start tick must be less than end tick.")
            ticks = list(range(start_tick, end_tick + 1))
            return ticks
        except Exception as e:
            print(f"An error occurred while getting the ticks between rounds: {e}")
            return None
    

    def get_player_movement_in_round(self, round):
        try:
            parser = process_demo(self.demo_path)
            round_ticks = self.get_ticks_between_rounds(round)
            position_fields = ["X", "Y", "Z"]
            df = parser.parse_ticks(position_fields, ticks=round_ticks)
            print(df)
        except Exception as e:
            print(f"An error occurred while getting player positions at round {round + 1}: {e}")
            return None

if __name__ == "__main__":
    print("Demos processing...")

    PATH = os.getenv("DEMO_PATH")
    dp = DemoProcessor(PATH)
    seed = 0
    rd = random.Random()
    rd.seed(seed)
    dp.set_demo_id(uuid.UUID(int=rd.getrandbits(128)))
    # dp.get_relevant_ticks_every_round(0)
    dp.get_player_movement_in_round(2)
    dp.get_game_leaderboard_every_round(12)