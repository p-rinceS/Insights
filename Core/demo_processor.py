import demoparser2
import pandas as pd
from demoparser2 import DemoParser

path = "../assets/demos/mirage.dem"

def process_demo(demo_path):
    try:
        parser = DemoParser(demo_path)
    except FileNotFoundError:
        raise FileNotFoundError(f"Demo file not found: {demo_path}")
    return parser

def process_demo_voices():
    try:
        parser = process_demo(path)
        parser.parse_header()
        print("Processing demo voices...")
        streamed_bytes = parser.parse_voice()
        for steam_id, raw_bytes in streamed_bytes.items():
            # Output the files in "../assets/output/voices/demo_name/steam_id.wav"
            #TODO eventually, this will not output to a file but to a database or similar storage
            with open(f"../assets/output/voices/{steam_id}.wav", "wb") as f:
                f.write(raw_bytes)
    except Exception as e:
        print(f"An error occurred while processing demo voices: {e}")

def extract_team_data(players, team_number):
    return players[players['team_number'] == team_number].apply(
        lambda row: {"name": row['name'], "steamid": row['steamid']}, axis=1
    ).tolist()
    
def get_player_teams():
    try:
        parser = DemoParser(path)
        parser.parse_header()
        players = parser.parse_player_info()
        teams = players['team_number'].unique()
        team1 = extract_team_data(players, teams[0])
        team2 = extract_team_data(players, teams[1])
        return team1, team2
    except Exception as e:
        print(f"An error occurred while getting player teams: {e}")
        return [], []

if __name__ == "__main__":
    # Example usage
    process_demo_voices()
    team1, team2 = get_player_teams()
    # Process demo
    parser = process_demo(path)
    parser.parse_header()
    print("Demo processed successfully.")