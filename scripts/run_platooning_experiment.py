#!/usr/bin/env python3
"""
Production Script: Platooning Experiments

Runs large-scale platooning simulations with:
- Multiple parameter combinations
- Parallel processing
- Progress tracking
- Confidence interval calculation
- Excel output

Usage:
    python scripts/run_platooning.py --help
    python scripts/run_platooning.py --dry-run
    python scripts/run_platooning.py --trials 30 --output-dir results/platooning
"""

import os
import sys
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
from platooning import run_platooning_simulation
from utils import CRRModifier, append_df_to_excel, sanitize_workbook


def simulate_one(slope, net, road, speed, rt, trial, base_cfg, base_phem_dir, crr_values):
    """
    Worker function for a single platooning trial.
    
    This function runs in a separate process for parallel execution.
    """
    cfg_path = None
    try:
        # Modify CRR (platooning uses .veh suffix)
        crr_modifier = CRRModifier(base_phem_dir, ".veh")
        crr_modifier.modify_crr_for_routes([rt], road, crr_values)
        
        # Generate unique config for this run
        cfg_path = SimulationBase.generate_config(base_cfg, rt, net, unique=True)
        
        # Run simulation
        rows = run_platooning_simulation(cfg_path, rt, speed)
        
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
        # Cleanup temporary config file
        if cfg_path and os.path.exists(cfg_path):
            try:
                os.remove(cfg_path)
            except:
                pass


def calculate_confidence_intervals(df, group_cols):
    """Calculate 95% confidence intervals for grouped data."""
    ci_records = []
    
    for keys, grp in df.groupby(group_cols):
        vals = grp['Fuel_L_per_100km'].dropna()
        if len(vals) < 2:
            continue
            
        mean = vals.mean()
        std = vals.std(ddof=1)
        n = len(vals)
        sem = std / np.sqrt(n)
        t_crit = stats.t.ppf(0.975, df=n-1)
        
        record = dict(zip(group_cols, keys if isinstance(keys, tuple) else [keys]))
        record.update({
            'Mean': mean,
            'CI_Lower': mean - t_crit * sem,
            'CI_Upper': mean + t_crit * sem,
            'Std': std,
            'SEM': sem,
            'N': n
        })
        ci_records.append(record)
    
    return pd.DataFrame(ci_records)


def main():
    parser = argparse.ArgumentParser(
        description="Run platooning experiments",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --dry-run                          # Show configuration
  %(prog)s --trials 30 --output-dir results   # Run with 30 trials
  %(prog)s --workers 50 --trials 10           # Use 50 parallel workers
        """
    )
    
    # Required paths
    parser.add_argument("--xodr-file", required=True,
                        help="Path to your OpenDRIVE (.xodr) file")
    parser.add_argument("--sumo-cfg", required=True,
                        help="Path to your base SUMO config (.sumocfg) file")
    parser.add_argument("--route-base-dir", required=True,
                        help="Path to your route templates folder (e.g., simulation/)")
    parser.add_argument("--phem-dir", required=True,
                        help="Path to your PHEMlight emissions folder")
    
    # Optional settings
    parser.add_argument("--output-dir", "-o", default="platooning_results",
                        help="Output directory (default: platooning_results)")
    parser.add_argument("--trials", "-t", type=int, default=30,
                        help="Number of trials per scenario (default: 30)")
    parser.add_argument("--workers", "-w", type=int, default=os.cpu_count(),
                        help="Number of parallel workers (default: CPU count)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show configuration without running")
    
    args = parser.parse_args()
    
    # =========================================================================
    # PARAMETERS - Modify these as needed
    # =========================================================================
    
    models = ["Model1", "Model2", "Model3", "Model4", "Model5"]
    truck_counts = [1, 2, 3]
    sigma_tau_pairs = [
        (0.5, 1.00), (0.4, 0.95), (0.3, 0.90),
        (0.2, 0.85), (0.0, 0.80), (0.0, 0.75)
    ]
    accel_values = [0.2, 0.4, 0.6, 0.8, 1.0]
    speeds_km_h = [30, 40, 60, 80, 90, 100]
    min_gap_values = [5.0, 10.0, 15.0, 20.0]
    slope_values = [0.0, 0.04, 0.06, 0.08, 0.10, 0.12, 0.16, 0.20]
    road_types = ['primary', 'secondary', 'cross_country']
    
    crr_values = {
        'primary': None,      # Use default from file
        'secondary': 0.010,
        'cross_country': 0.025
    }
    
    # =========================================================================
    # DRY RUN - Show configuration
    # =========================================================================
    
    if args.dry_run:
        print("=" * 60)
        print("DRY RUN - Configuration")
        print("=" * 60)
        print(f"\nPaths:")
        print(f"  OpenDRIVE file:  {args.xodr_file}")
        print(f"  SUMO config:     {args.sumo_cfg}")
        print(f"  Route base dir:  {args.route_base_dir}")
        print(f"  PHEMlight dir:   {args.phem_dir}")
        print(f"  Output dir:      {args.output_dir}")
        print(f"\nParameters:")
        print(f"  Models:       {models}")
        print(f"  Truck counts: {truck_counts}")
        print(f"  Speeds:       {speeds_km_h}")
        print(f"  Slopes:       {slope_values}")
        print(f"  Min gaps:     {min_gap_values}")
        print(f"  Road types:   {road_types}")
        print(f"\nExecution:")
        print(f"  Trials:       {args.trials}")
        print(f"  Workers:      {args.workers}")
        
        # Calculate total scenarios
        n_routes = len(models) * len(truck_counts) * 2 * len(sigma_tau_pairs) * len(accel_values)  # 2 = lower/upper
        n_scenarios = len(slope_values) * len(road_types) * len(speeds_km_h) * n_routes
        n_total = n_scenarios * args.trials
        print(f"\nEstimated total simulations: {n_total:,}")
        return
    
    # =========================================================================
    # SETUP
    # =========================================================================
    
    os.makedirs(args.output_dir, exist_ok=True)
    raw_file = os.path.join(args.output_dir, "platooning_raw.xlsx")
    ci_file = os.path.join(args.output_dir, "platooning_ci.xlsx")
    
    # Clean up any corrupted files
    sanitize_workbook(raw_file)
    sanitize_workbook(ci_file)
    
    print("=" * 60)
    print("PLATOONING EXPERIMENT")
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
    route_files = route_gen.generate_platooning_routes(
        models, truck_counts, min_gap_values, sigma_tau_pairs, accel_values
    )
    print(f"      Generated {len(route_files)} route files")
    
    # =========================================================================
    # STEP 3: Run Simulations
    # =========================================================================
    
    print("\n[3/4] Running simulations...")
    
    all_results = []
    total_scenarios = len(networks) * len(road_types) * len(speeds_km_h)
    
    with tqdm(total=total_scenarios, desc="Scenarios", unit="scenario") as pbar:
        for slope_val, net in networks:
            for road in road_types:
                for speed in speeds_km_h:
                    pbar.set_postfix({
                        'slope': slope_val,
                        'road': road,
                        'speed': speed
                    })
                    
                    # Build task list
                    tasks = [
                        (slope_val, net, road, speed, rt, trial,
                         args.sumo_cfg, args.phem_dir, crr_values)
                        for rt in route_files
                        for trial in range(1, args.trials + 1)
                    ]
                    
                    # Run in parallel
                    scenario_rows = []
                    with ProcessPoolExecutor(max_workers=args.workers) as executor:
                        futures = [executor.submit(simulate_one, *t) for t in tasks]
                        for future in as_completed(futures):
                            rows = future.result()
                            if rows:
                                scenario_rows.extend(rows)
                    
                    # Save raw results
                    if scenario_rows:
                        df_raw = pd.DataFrame(scenario_rows)
                        append_df_to_excel(df_raw, raw_file, "Raw")
                        all_results.extend(scenario_rows)
                    
                    pbar.update(1)
    
    # =========================================================================
    # STEP 4: Calculate Confidence Intervals
    # =========================================================================
    
    print("\n[4/4] Calculating confidence intervals...")
    
    if all_results:
        df = pd.DataFrame(all_results)
        group_cols = ['Slope', 'RoadType', 'Speed', 'Model', 'Count', 'Vehicle']
        df_ci = calculate_confidence_intervals(df, group_cols)
        
        if not df_ci.empty:
            append_df_to_excel(df_ci, ci_file, "CI")
            print(f"      Calculated CI for {len(df_ci)} groups")
    
    # =========================================================================
    # DONE
    # =========================================================================
    
    print("\n" + "=" * 60)
    print("DONE!")
    print("=" * 60)
    print(f"\nResults saved to: {args.output_dir}/")
    print(f"  - platooning_raw.xlsx  (raw data)")
    print(f"  - platooning_ci.xlsx   (confidence intervals)")


if __name__ == "__main__":
    main()
