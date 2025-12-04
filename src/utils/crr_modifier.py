"""
Rolling resistance coefficient (CRR) modification for PHEMlight emission files.
"""

import os
import re
from typing import Dict, List, Optional


class CRRModifier:
    """Modifies CRR values in PHEMlight vehicle emission files."""
    
    DEFAULT_CRR_VALUES = {
        'primary': None,  # Use default
        'secondary': 0.010,
        'cross_country': 0.025,
    }
    
    def __init__(self, base_phem_dir: str):
        """
        Args:
            base_phem_dir: Base directory for PHEMlight emission files
        """
        self.base_phem_dir = base_phem_dir
    
    def modify_crr_for_routes(
        self,
        route_files: List[str],
        road_type: str,
        crr_values: Optional[Dict[str, float]] = None
    ) -> None:
        """
        Modify CRR for all emission classes found in route files.
        """
        if crr_values is None:
            crr_values = self.DEFAULT_CRR_VALUES
        
        crr = crr_values.get(road_type)
        if crr is None:
            return
        
        # Extract emission classes from route files
        emission_classes = set()
        for route_file in route_files:
            if not os.path.exists(route_file):
                continue
            with open(route_file, 'r') as f:
                content = f.read()
            classes = re.findall(r'emissionClass="([^\"]+)"', content)
            emission_classes.update(classes)
        
        # Modify each emission class file
        for cls in emission_classes:
            self._modify_vehicle_file(cls, crr)
    
    def _modify_vehicle_file(self, emission_class: str, crr: float) -> bool:
        """Modify CRR in a single vehicle file."""
        veh_path = os.path.join(self.base_phem_dir, emission_class + ".veh")
        
        if not os.path.isfile(veh_path):
            print(f"NOT FOUND: {veh_path}")
            return False
        
        with open(veh_path, 'r') as f:
            lines = f.read().splitlines()
        
        new_lines = []
        skip = False
        
        for line in lines:
            if skip:
                skip = False
                continue
            if line.strip().lower() == 'c fr0':
                new_lines.append(line)
                new_lines.append(str(crr))
                skip = True
            else:
                new_lines.append(line)
        
        with open(veh_path, 'w') as f:
            f.write("\n".join(new_lines))
        
        print(f"Modified CRR in: {veh_path} to {crr}")
        return True
