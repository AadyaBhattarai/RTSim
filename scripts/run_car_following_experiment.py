#!/usr/bin/env python3
"""
Production Script: Car Following Experiments

Runs large-scale car following simulations with:
- Multiple parameter combinations
- Parallel processing
- Progress tracking
- Per-model confidence interval files
- Excel output

Usage:
    python scripts/run_car_following.py --help
    python scripts/run_car_following.py --dry-run
    python scripts/run_car_following.py --trials 10 --output-dir results/car_following
"""

import os
import sys
import re
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np
import pandas as pd
from scipy import stats
from tqdm import tqdm

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import from our modules
from core import SimulationBase, NetworkGenerator, RouteGenerator
from car_following import run_car_following_simulation
from utils import CRRModifier, append_df_to_excel, sanitize_workbook


def simulate_one(slope, net, road, rt, trial, base_cfg, base_phem_dir, crr_values):
    """
    Worker function for a single car following trial.
    
    Note: trial is used as seed for SUMO's randomization.
    """
    cfg_path = None
    try:
        # Modify CRR (car following uses .PHEMLight.veh suffix)
        crr_modifier = CRRModifier(base_phem_dir, ".PHEMLight.veh")
        crr_modifier.modify_crr_for_routes([rt], road, crr_values)
        
        # Generate unique config
        cfg_path = SimulationBase.generate_config(base_cfg, rt, net, unique=True)
        
        # Run simulation (trial = seed)
        rows = run_car_following_simulation(cfg_path, rt, seed=trial)
        
        # Add metadata
        for r in rows:
            r.update({
                'Slope': slope,
                'RoadType': road,
                'Trial': trial
            })
        
        return rows
        
    except Exception as e:
        print(f"\n[ERROR] Trial {trial} failed: {e}")
        return []
        
    finally:
        if cfg_path and os.path.exists(cfg_path):
            try:
                os.remove(cfg_path)
            except:
                pass


def get_model_from_route(route_file):
    """Extract model name from route filename."""
    basename = os.path.basename(route_file)
    match = re.match(r'route_(\w+)_', basename)
    return match.group(1) if match else "Unknown"


def main():
    parser = argparse.ArgumentParser(
        description="Run car following experiments",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --dry-run                          # Show configuration
  %(prog)s --trials 10 --output-dir results   # Run with 10 trials
  %(prog)s --workers 50 --trials 10           # Use 50 parallel workers
        """
    )
    
    # Required paths
    parser.add_argument("--xodr-file", required=True,
                        help="Path to your OpenDRIVE (.xodr) file")
    parser.add_argument("--sumo-cfg", required=True,
                        help="Path to your base SUMO config (.sumocfg) file")
    parser.add_argument("--route-base-dir", required=True,
                        help="Path to your car following route templates folder")
    parser.add_argument("--phem-dir", required=True,
                        help="Path to your emissions folder")
    
    # Optional settings
    parser.add_argument("--output-dir", "-o", default="car_following_results",
                        help="Output directory (default: car_following_results)")
    parser.add_argument("--trials", "-t", type=int, default=10,
                        help="Number of trials per scenario (default: 10)")
    parser.add_argument("--workers", "-w", type=int, default=50,
                        help="Number of parallel workers (default: 50)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show configuration without running")
    
    args = parser.parse_args()
    
    # =========================================================================
    # PARAMETERS - Modify these as needed
    # =========================================================================
    
    models = ["Model4", "Model5"]
    truck_counts = [1]  # Single truck for car following
    sigma_tau_pairs = [
        (0.5, 1.00), (0.4, 0.95), (0.3, 0.90),
        (0.2, 0.85), (0.0, 0.80), (0.0, 0.75)
    ]
    accel_values = [0.2, 0.6, 1.0]
    speeds_km_h = [30, 60, 90, 100]
    min_gap_values = [5, 10, 15, 20]
    slope_values = [0.0, 0.06, 0.08, 0.16, 0.20]
    road_types = ['cross_country']
    
    crr_values = {
        'primary': 0.006923,
        'secondary': 0.010,
        'cross_country': 0.025
    }
    
    # =========================================================================
    # DRY RUN
    # =========================================================================
    
    if args.dry_run:
        print("=" * 60)
        print("DRY RUN - Configuration")
        print("=" * 60)
        print(f"\nPaths:")
        print(f"  OpenDRIVE file:  {args.xodr_file}")
        print(f"  SUMO config:     {args.sumo_cfg}")
        print(f"  Route base dir:  {args.route_base_dir}")
        print(f"  Emissions dir:   {args.phem_dir}")
        print(f"  Output dir:      {args.output_dir}")
        print(f"\nParameters:")
        print(f"  Models:       {models}")
        print(f"  Truck counts: {truck_counts}")
        print(f"  Speeds:       {speeds_km_h}")
        print(f"  Slopes:       {slope_values}")
        print(f"  Road types:   {road_types}")
        print(f"\nExecution:")
        print(f"  Trials:       {args.trials}")
        print(f"  Workers:      {args.workers}")
        return
    
    # =========================================================================
    # SETUP
    # =========================================================================
    
    os.makedirs(args.output_dir, exist_ok=True)
    raw_file = os.path.join(args.output_dir, "all_scenarios_raw.xlsx")
    
    sanitize_workbook(raw_file)
    for model in models:
        sanitize_workbook(os.path.join(args.output_dir, f"confidence_intervals_{model}.xlsx"))
    
    print("=" * 60)
    print("CAR FOLLOWING EXPERIMENT")
    print("=" * 60)
    
    # =========================================================================
    # STEP 1: Generate Networks
    # =========================================================================
    
    print("\n[1/4] Generating networks...")
    net_gen = NetworkGenerator(os.path.join(args.output_dir, "networks"))
    networks = net_gen.generate_networks(args.xodr_file, "network", slope_values)
    print(f"      Generated {len(networks)} network files")
    
    # =========================================================================
    # STEP 2: Generate Routes
    # =========================================================================
    
    print("\n[2/4] Generating route files...")
    route_gen = RouteGenerator(args.route_base_dir, os.path.join(args.output_dir, "routes"))
    route_files = route_gen.generate_car_following_routes(
        models, truck_counts, sigma_tau_pairs, accel_values, speeds_km_h, min_gap_values
    )
    print(f"      Generated {len(route_files)} route files")
    
    # =========================================================================
    # STEP 3: Build Scenario List
    # =========================================================================
    
    print("\n[3/4] Running simulations...")
    
    # Build scenario parameter combinations
    scenario_list = []
    for slope_val, net in networks:
        for road in road_types:
            for speed in speeds_km_h:
                for sigma, tau in sigma_tau_pairs:
                    for accel in accel_values:
                        scenario_list.append({
                            'slope': slope_val,
                            'net': net,
                            'road': road,
                            'speed': speed,
                            'sigma': sigma,
                            'tau': tau,
                            'accel': accel
                        })
    
    # =========================================================================
    # STEP 4: Run Simulations
    # =========================================================================
    
    model_results = {m: [] for m in models}
    
    with tqdm(total=len(scenario_list), desc="Scenarios", unit="scenario") as pbar:
        for scenario in scenario_list:
            pbar.set_postfix({
                'slope': scenario['slope'],
                'speed': scenario['speed']
            })
            
            # Find matching route files for this scenario
            matching_routes = []
            for rt in route_files:
                name = os.path.basename(rt)
                if (f"sigma_{scenario['sigma']}" in name and
                    f"tau_{scenario['tau']}" in name and
                    f"accel_{scenario['accel']}" in name and
                    f"maxSpeed_{scenario['speed']}" in name):
                    matching_routes.append(rt)
            
            if not matching_routes:
                pbar.update(1)
                continue
            
            # Modify CRR for all routes in this scenario
            crr_modifier = CRRModifier(args.phem_dir, ".PHEMLight.veh")
            crr_modifier.modify_crr_for_routes(matching_routes, scenario['road'], crr_values)
            
            # Build tasks
            tasks = []
            for rt in matching_routes:
                for trial in range(1, args.trials + 1):
                    tasks.append((
                        scenario['slope'], scenario['net'], scenario['road'],
                        rt, trial, args.sumo_cfg, args.phem_dir, crr_values
                    ))
            
            # Run in parallel
            with ProcessPoolExecutor(max_workers=args.workers) as executor:
                futures = []
                for task in tasks:
                    rt = task[3]
                    model = get_model_from_route(rt)
                    fut = executor.submit(simulate_one, *task)
                    futures.append((fut, model))
                
                for fut, model in futures:
                    rows = fut.result()
                    if rows:
                        for r in rows:
                            r['Model'] = model
                        model_results[model].extend(rows)
                        
                        # Save raw data
                        df_raw = pd.DataFrame(rows)
                        append_df_to_excel(df_raw, raw_file, "Raw")
            
            pbar.update(1)
    
    # =========================================================================
    # STEP 5: Calculate Confidence Intervals (per model)
    # =========================================================================
    
    print("\n[4/4] Calculating confidence intervals...")
    
    for model in models:
        rows = model_results[model]
        if len(rows) < 20:
            print(f"      Warning: {model} has only {len(rows)} rows")
            continue
        
        df = pd.DataFrame(rows)
        ci_records = []
        
        for veh_id, grp in df.groupby('Vehicle'):
            vals = grp['Fuel_L_per_100km'].dropna()
            if len(vals) < 2:
                continue
                
            mean = vals.mean()
            std = vals.std(ddof=1)
            n = len(vals)
            sem = std / np.sqrt(n)
            t_crit = stats.t.ppf(0.975, df=n-1)
            
            # Get scenario info from first row
            first = grp.iloc[0]
            ci_records.append({
                'Model': model,
                'Slope': first['Slope'],
                'RoadType': first['RoadType'],
                'Speed': first['Speed'],
                'Sigma': first['Sigma'],
                'Tau': first['Tau'],
                'Accel': first['Accel'],
                'Vehicle': veh_id,
                'Mean': mean,
                'CI_Lower': mean - t_crit * sem,
                'CI_Upper': mean + t_crit * sem,
                'Std': std,
                'SEM': sem,
                'N': n
            })
        
        if ci_records:
            ci_file = os.path.join(args.output_dir, f"confidence_intervals_{model}.xlsx")
            df_ci = pd.DataFrame(ci_records)
            append_df_to_excel(df_ci, ci_file, "CI")
            print(f"      {model}: {len(ci_records)} CI records")
    
    # =========================================================================
    # DONE
    # =========================================================================
    
    print("\n" + "=" * 60)
    print("DONE!")
    print("=" * 60)
    print(f"\nResults saved to: {args.output_dir}/")
    print(f"  - all_scenarios_raw.xlsx")
    for model in models:
        print(f"  - confidence_intervals_{model}.xlsx")


if __name__ == "__main__":
    main()
