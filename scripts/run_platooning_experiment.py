#!/usr/bin/env python3
"""
Production Script: Platooning Experiments

Runs large-scale platooning simulations with parallel processing.

Workflow:
    1. Generate SUMO networks (one per slope value)
    2. Generate route files from templates
    3. For each scenario (slope × road × speed × gap × sigma/tau × accel):
       a. Modify CRR in .veh files for the road type (BEFORE workers launch)
       b. Run N trials in parallel using ProcessPoolExecutor
       c. Collect results and compute confidence intervals
    4. Save raw data and CI to Excel files

Usage:
    python scripts/run_platooning_experiment.py \\
        --xodr-file data/opendrive/experiment_e.xodr \\
        --sumo-cfg data/sumo/configs/grade0.sumocfg \\
        --route-base-dir data/sumo/routes/platooning/ \\
        --phem-dir $SUMO_HOME/data/emissions \\
        --trials 20 --workers 50 --output-dir results/platooning
"""

import os
import sys
import re
import argparse
from concurrent.futures import ProcessPoolExecutor
from typing import List, Dict

import numpy as np
import pandas as pd
from scipy import stats
from tqdm import tqdm

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core import SimulationBase, NetworkGenerator, RouteGenerator
from src.platooning import run_platooning_simulation
from src.utils import CRRModifier, append_df_to_excel, sanitize_workbook


def simulate_one(slope, net, road, speed, rt, trial, base_cfg):
    """
    Worker function for a single platooning trial.
    Runs in a separate process via ProcessPoolExecutor.
    """
    cfg_path = None
    try:
        cfg_path = SimulationBase.generate_config(base_cfg, rt, net)
        rows = run_platooning_simulation(cfg_path, rt, speed)
        for r in rows:
            r.update({'Slope': slope, 'RoadType': road})
        return rows
    except Exception as e:
        print(f"\n  [ERROR] Trial {trial} failed: {e}")
        return []
    finally:
        if cfg_path and os.path.exists(cfg_path):
            try:
                os.remove(cfg_path)
            except Exception:
                pass


def find_route_file(
    all_routes: List[str], model: str, variant: str,
    min_gap: float, sigma: float, tau: float, accel: float
) -> str:
    """Find a matching route file from the generated list."""
    for candidate in all_routes:
        name = os.path.basename(candidate)
        if (f"route_{model}_" in name and
            f"_minGap_{min_gap}_" in name and
            f"_tau_{tau}" in name and
            f"_accel_{accel}" in name and
            f"_sigma_{sigma}" in name and
            f"_{variant}_" in name):
            return candidate
    return None


def main():
    parser = argparse.ArgumentParser(
        description="Run platooning experiments with parallel processing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--xodr-file", required=True, help="OpenDRIVE (.xodr) file")
    parser.add_argument("--sumo-cfg", required=True, help="Base SUMO config (.sumocfg)")
    parser.add_argument("--route-base-dir", required=True, help="Route templates directory")
    parser.add_argument("--phem-dir", required=True, help="PHEMlight emissions directory")
    parser.add_argument("--output-dir", "-o", default="platooning_results")
    parser.add_argument("--trials", "-t", type=int, default=20)
    parser.add_argument("--workers", "-w", type=int, default=os.cpu_count())
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    # =========================================================================
    # PARAMETERS — Modify these for your experiment
    # =========================================================================
    models = ["Model1", "Model2"]
    truck_counts = [1, 2, 3]
    sigma_tau_pairs = [
        (0.5, 1.00), (0.4, 0.95), (0.3, 0.90),
        (0.2, 0.85), (0.0, 0.80), (0.0, 0.75),
    ]
    accel_values = [0.2, 0.6, 1.0]
    speeds_km_h = [30, 60, 90, 100]
    min_gap_values = [5.0, 10.0, 15.0, 20.0]
    slope_values = [0.0, 0.06, 0.08, 0.16, 0.20]
    road_types = ['primary', 'secondary', 'cross_country']
    crr_values = {'primary': 0.006923, 'secondary': 0.010, 'cross_country': 0.025}

    if args.dry_run:
        print("DRY RUN — Configuration:")
        print(f"  Models:     {models}")
        print(f"  Trucks:     {truck_counts}")
        print(f"  Speeds:     {speeds_km_h}")
        print(f"  Slopes:     {slope_values}")
        print(f"  Gaps:       {min_gap_values}")
        print(f"  Roads:      {road_types}")
        print(f"  Trials:     {args.trials}")
        print(f"  Workers:    {args.workers}")
        return

    # =========================================================================
    # SETUP
    # =========================================================================
    os.makedirs(args.output_dir, exist_ok=True)
    raw_file = os.path.join(args.output_dir, "platooning_raw.xlsx")
    sanitize_workbook(raw_file)
    for model in models:
        sanitize_workbook(os.path.join(args.output_dir, f"platooning_ci_{model}.xlsx"))

    # =========================================================================
    # STEP 1: Generate networks
    # =========================================================================
    print("[1/4] Generating networks...")
    net_gen = NetworkGenerator(os.path.join(args.output_dir, "networks"))
    networks = net_gen.generate_networks(args.xodr_file, "network", slope_values)

    # =========================================================================
    # STEP 2: Generate route files
    # =========================================================================
    print("[2/4] Generating route files...")
    route_gen = RouteGenerator(args.route_base_dir, os.path.join(args.output_dir, "routes"))
    all_routes = route_gen.generate_platooning_routes(
        models, truck_counts, min_gap_values, sigma_tau_pairs, accel_values
    )

    # =========================================================================
    # STEP 3: Build and run scenarios
    # =========================================================================
    print("[3/4] Running simulations...")

    scenario_list = []
    for slope_val, net in networks:
        for road in road_types:
            for speed in speeds_km_h:
                for gap in min_gap_values:
                    for sigma, tau in sigma_tau_pairs:
                        for accel in accel_values:
                            scenario_list.append({
                                'slope': slope_val, 'net': net, 'road': road,
                                'speed': speed, 'minGap': gap,
                                'sigma': sigma, 'tau': tau, 'accel': accel,
                            })

    scenario_bar = tqdm(total=len(scenario_list), desc="Scenarios")

    for scenario in scenario_list:
        # --- Collect route files for this scenario ---
        route_files = []
        for variant in ['lower', 'upper']:
            for model in models:
                rt = find_route_file(
                    all_routes, model, variant,
                    scenario['minGap'], scenario['sigma'],
                    scenario['tau'], scenario['accel']
                )
                if rt:
                    route_files.append(rt)

        if not route_files:
            scenario_bar.update(1)
            continue

        # --- Modify CRR BEFORE launching parallel workers ---
        crr_mod = CRRModifier(args.phem_dir, ".veh")
        crr_mod.modify_crr_for_routes(route_files, scenario['road'], crr_values)

        # --- Run trials in parallel ---
        model_results: Dict[str, list] = {m: [] for m in models}

        for variant in ['lower', 'upper']:
            jobs = []
            for model in models:
                rt = find_route_file(
                    all_routes, model, variant,
                    scenario['minGap'], scenario['sigma'],
                    scenario['tau'], scenario['accel']
                )
                if not rt:
                    continue
                for trial in range(1, args.trials + 1):
                    jobs.append((model, rt, trial))

            if not jobs:
                continue

            with ProcessPoolExecutor(max_workers=args.workers) as executor:
                futures = []
                for model, rt, trial in jobs:
                    fut = executor.submit(
                        simulate_one, scenario['slope'], scenario['net'],
                        scenario['road'], scenario['speed'], rt, trial,
                        args.sumo_cfg
                    )
                    futures.append((fut, model))

                for fut, model in futures:
                    rows = fut.result()
                    if rows:
                        for r in rows:
                            r['Model'] = model
                        model_results[model].extend(rows)

        # --- Compute confidence intervals per model ---
        for model in models:
            all_rows = model_results[model]
            if len(all_rows) < 2:
                continue

            df = pd.DataFrame(all_rows)
            ci_records = []

            for veh_id, grp in df.groupby('Vehicle'):
                vals = grp['Fuel_L_per_100km'].dropna()
                if len(vals) < 2:
                    continue
                mean = np.nanmean(vals)
                std = np.nanstd(vals, ddof=1)
                n = len(vals)
                sem = std / np.sqrt(n)
                t_crit = stats.t.ppf(0.975, df=n - 1)

                ci_records.append({
                    **scenario, 'Model': model, 'Vehicle': veh_id,
                    'Mean': mean,
                    'CI_Lower': mean - t_crit * sem,
                    'CI_Upper': mean + t_crit * sem,
                    'Std': std, 'SEM': sem, 'N': n,
                })

            if ci_records:
                ci_file = os.path.join(args.output_dir, f"platooning_ci_{model}.xlsx")
                append_df_to_excel(pd.DataFrame(ci_records), ci_file, "CI")

            if all_rows:
                append_df_to_excel(pd.DataFrame(all_rows), raw_file, "Raw")

        scenario_bar.update(1)

    scenario_bar.close()

    # =========================================================================
    # DONE
    # =========================================================================
    print(f"\n[4/4] Done! Results saved to: {args.output_dir}/")


if __name__ == "__main__":
    main()
