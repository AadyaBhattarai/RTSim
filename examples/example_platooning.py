#!/usr/bin/env python3
"""
Example: Running a Platooning Simulation

This example shows how to use the modules to run a platooning simulation
using the example route file and PHEMlight emission files.

Prerequisites:
- SUMO installed and SUMO_HOME set
- Plexe installed
- utils7.py in your Python path
"""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import our modules
from core import SimulationBase, NetworkGenerator, RouteGenerator
from platooning import run_platooning_simulation
from utils import CRRModifier, append_df_to_excel, sanitize_workbook

import pandas as pd


def main():
    # =========================================================================
    # CONFIGURATION - Modify these paths to match your setup
    # =========================================================================
    
    # Your OpenDRIVE file (defines road geometry)
    xodr_file = "experiment_e.xodr"
    
    # Your base SUMO config file
    sumo_cfg = "grade0.sumocfg"
    
    # Your route templates folder (contains Model1/2truck/90/5/lower/grade01.rou.xml)
    route_base_dir = "examples/simulation"
    
    # Your PHEMlight emissions folder
    phem_dir = "examples/PHEMlight"
    
    # Output directory
    output_dir = "example_results"
    os.makedirs(output_dir, exist_ok=True)
    
    # =========================================================================
    # PARAMETERS - Customize as needed
    # =========================================================================
    
    models = ["Model1"]              # Your model names (folder names)
    truck_counts = [2]               # Number of trucks in platoon
    min_gaps = [5.0]                 # Gap between trucks (meters)
    sigma_tau_pairs = [(0.5, 1.0)]   # (sigma, tau) pairs
    accel_values = [0.6]             # Acceleration values
    speeds_km_h = [90]               # Speed in km/h
    slope_values = [0.0, 0.04]       # Road slopes to test
    road_type = "primary"            # Road type for CRR
    trials = 3                       # Number of trials per scenario
    
    # CRR values for different road types
    crr_values = {
        'primary': 0.006923,
        'secondary': 0.010,
        'cross_country': 0.025
    }
    
    # =========================================================================
    # STEP 1: Generate Networks (one per slope value)
    # =========================================================================
    
    print("=" * 60)
    print("STEP 1: Generating networks from OpenDRIVE file")
    print("=" * 60)
    
    net_gen = NetworkGenerator(os.path.join(output_dir, "networks"))
    networks = net_gen.generate_networks(xodr_file, "network", slope_values)
    
    for slope, net_path in networks:
        print(f"  Generated: slope={slope} -> {net_path}")
    
    # =========================================================================
    # STEP 2: Generate Route Files
    # =========================================================================
    
    print("\n" + "=" * 60)
    print("STEP 2: Generating route files")
    print("=" * 60)
    
    route_gen = RouteGenerator(route_base_dir, os.path.join(output_dir, "routes"))
    route_files = route_gen.generate_platooning_routes(
        models=models,
        truck_counts=truck_counts,
        min_gaps=min_gaps,
        sigma_tau_pairs=sigma_tau_pairs,
        accels=accel_values
    )
    
    print(f"  Generated {len(route_files)} route files")
    for rt in route_files[:3]:  # Show first 3
        print(f"    - {os.path.basename(rt)}")
    
    # =========================================================================
    # STEP 3: Modify CRR in PHEMlight Files
    # =========================================================================
    
    print("\n" + "=" * 60)
    print("STEP 3: Modifying CRR values in PHEMlight files")
    print("=" * 60)
    
    crr_modifier = CRRModifier(phem_dir, ".veh")
    crr_modifier.modify_crr_for_routes(route_files, road_type, crr_values)
    
    # =========================================================================
    # STEP 4: Run Simulations
    # =========================================================================
    
    print("\n" + "=" * 60)
    print("STEP 4: Running simulations")
    print("=" * 60)
    
    all_results = []
    
    for slope, net_path in networks:
        for speed in speeds_km_h:
            for route_file in route_files:
                for trial in range(1, trials + 1):
                    print(f"\n  Running: slope={slope}, speed={speed}, trial={trial}")
                    print(f"    Route: {os.path.basename(route_file)}")
                    
                    try:
                        # Generate unique config for this run
                        cfg_path = SimulationBase.generate_config(
                            sumo_cfg, route_file, net_path, unique=True
                        )
                        
                        # Run the simulation
                        results = run_platooning_simulation(cfg_path, route_file, speed)
                        
                        # Add metadata
                        for r in results:
                            r['Slope'] = slope
                            r['RoadType'] = road_type
                            r['Trial'] = trial
                        
                        all_results.extend(results)
                        
                        # Print results
                        for r in results:
                            print(f"    Vehicle {r['Vehicle']}: {r['Fuel_L_per_100km']:.2f} L/100km")
                        
                        # Cleanup temp config
                        if os.path.exists(cfg_path):
                            os.remove(cfg_path)
                            
                    except Exception as e:
                        print(f"    ERROR: {e}")
    
    # =========================================================================
    # STEP 5: Save Results
    # =========================================================================
    
    print("\n" + "=" * 60)
    print("STEP 5: Saving results")
    print("=" * 60)
    
    if all_results:
        df = pd.DataFrame(all_results)
        output_file = os.path.join(output_dir, "simulation_results.xlsx")
        sanitize_workbook(output_file)
        append_df_to_excel(df, output_file, "Results")
        print(f"  Saved to: {output_file}")
        
        # Print summary
        print("\n  Summary:")
        print(f"    Total runs: {len(all_results)}")
        print(f"    Mean fuel consumption: {df['Fuel_L_per_100km'].mean():.2f} L/100km")
    else:
        print("  No results to save")
    
    print("\n" + "=" * 60)
    print("DONE!")
    print("=" * 60)


if __name__ == "__main__":
    main()
