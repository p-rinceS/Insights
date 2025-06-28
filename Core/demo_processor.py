import demoparser2
from demoparser2.demoparser2 import DemoParser

path = "../assets/demos/nuke.dem"

def process_demo(demo_path):
    try:
        parser = DemoParser(demo_path)
        return parser
    finally:
        print("Demo processing complete.")


def process_demo_voices():
    try:
        parser = process_demo(path)
        parser.parse_header()
        print("Processing demo voices...")
        streamed_bytes = parser.parse_voice()
        for steam_id, raw_bytes in streamed_bytes.items():
            # Output the files in "../assets/output/voices/demo_name/steam_id.wav"
            with open(f"../assets/output/voices/{steam_id}.wav", "wb") as f:
                f.write(raw_bytes)
    except Exception as e:
        print(f"An error occurred while processing demo voices: {e}")

if __name__ == "__main__":
    process_demo_voices()
    print("All demo voices processed successfully.")
