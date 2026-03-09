"""
Rolling resistance (CRR) modifier for PHEMlight .veh files.

Before each simulation batch, the Fr0 value in the PHEMlight .veh files
must be set to match the road type being simulated:
    - Primary (highway):     Fr0 = 0.006923
    - Secondary (arterial):  Fr0 = 0.010
    - Cross-country (gravel): Fr0 = 0.025

This module extracts emission class paths from route files, locates
the corresponding .veh files, and modifies the Fr0 value in-place.

IMPORTANT: This must be called BEFORE launching parallel simulation
workers, not inside them, to avoid race conditions on shared .veh files.
"""

import os
import re
from typing import Dict, List, Optional


# Default rolling resistance coefficients
DEFAULT_CRR_VALUES = {
    'primary': 0.006923,
    'secondary': 0.010,
    'cross_country': 0.025,
}


class CRRModifier:
    """Modifies rolling resistance in PHEMlight vehicle emission files."""

    def __init__(self, phem_base_dir: str, veh_suffix: str = ".veh"):
        """
        Args:
            phem_base_dir: Root directory of PHEMlight emission files
                           (e.g., $SUMO_HOME/data/emissions)
            veh_suffix:    File suffix for vehicle files.
                           Platooning uses '.veh'
                           Car-following uses '.PHEMLight.veh'
        """
        self.phem_base_dir = phem_base_dir
        self.veh_suffix = veh_suffix

    def modify_crr_for_routes(
        self,
        route_files: List[str],
        road_type: str,
        crr_values: Optional[Dict[str, float]] = None
    ) -> int:
        """
        Modify Fr0 in all .veh files referenced by the given route files.

        Args:
            route_files: List of route file paths to scan for emission classes
            road_type:   Road type key ('primary', 'secondary', 'cross_country')
            crr_values:  Dict of road_type -> Fr0 value (uses defaults if None)

        Returns:
            Number of .veh files modified
        """
        if crr_values is None:
            crr_values = DEFAULT_CRR_VALUES

        crr = crr_values.get(road_type)
        if crr is None:
            print(f"  No CRR value for road type '{road_type}', skipping")
            return 0

        # Extract emission class paths from all route files
        emission_classes = set()
        for rt in route_files:
            with open(rt, 'r') as f:
                content = f.read()
            classes = re.findall(r'emissionClass="([^"]+)"', content)
            emission_classes.update(classes)

        # Modify each .veh file
        modified = 0
        for cls in emission_classes:
            veh_path = os.path.join(self.phem_base_dir, cls + self.veh_suffix)

            if not os.path.isfile(veh_path):
                print(f"  Warning: .veh file not found: {veh_path}")
                continue

            self._modify_fr0(veh_path, crr)
            modified += 1

        if modified:
            print(f"  Modified Fr0={crr} in {modified} .veh files for {road_type}")

        return modified

    @staticmethod
    def _modify_fr0(veh_path: str, new_fr0: float) -> None:
        """
        Replace the Fr0 value in a PHEMlight .veh file.

        The file format has:
            c Fr0
            0.006923    <- this line gets replaced
        """
        with open(veh_path, 'r') as f:
            lines = f.read().splitlines()

        new_lines = []
        skip_next = False

        for line in lines:
            if skip_next:
                new_lines.append(str(new_fr0))
                skip_next = False
                continue
            if line.strip().lower() == 'c fr0':
                new_lines.append(line)
                skip_next = True
            else:
                new_lines.append(line)

        with open(veh_path, 'w') as f:
            f.write('\n'.join(new_lines))
