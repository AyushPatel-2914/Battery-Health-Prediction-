import os
import pickle

map_dir = os.path.abspath("./MAP")
print(f"MAP dir: {map_dir}")
print(f"MAP dir exists: {os.path.isdir(map_dir)}")

waypoints_path = os.path.join(map_dir, 'waypoints.pkl')
print(f"waypoints.pkl path: {waypoints_path}")
print(f"waypoints.pkl exists: {os.path.exists(waypoints_path)}")

if os.path.exists(waypoints_path):
    try:
        with open(waypoints_path, 'rb') as f:
            waypoints_map = pickle.load(f)
        print(f"Successfully loaded waypoints_map")
        print(f"Number of chains: {len(waypoints_map)}")
        for i, (chain_key, chain_points) in enumerate(waypoints_map.items()):
            if i < 3:
                print(f"  Chain {i}: {len(chain_points)} points")
        
        # Concatenate all
        all_waypoints = []
        for chain_waypoints in waypoints_map.values():
            if chain_waypoints:
                all_waypoints.extend(chain_waypoints)
        print(f"Total waypoints: {len(all_waypoints)}")
    except Exception as e:
        print(f"Failed to load: {e}")
