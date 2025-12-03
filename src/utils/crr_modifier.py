"""Utilities for modifying rolling resistance coefficients in PHEMLight files."""
import os
import re
import shutil
from typing import Dict, List

class CRRModifier:
    """Manages modification and restoration of CRR values in vehicle emission files."""
    
    def __init__(self, base_phem_dir: str):
        self.base_phem_dir = base_phem_dir
        self.crr_values = {
            'primary': None,
            'secondary': 0.010,
            'cross_country': 0.025
        }
    
    def modify_route_file(self, route_file: str, road_type: str) -> List[str]:
        """
        Modify CRR values for all vehicles in a route file.
        
        Args:
            route_file: Path to the SUMO route file
            road_type: Type of road (primary, secondary, cross_country)
            
        Returns:
            List of modified vehicle file paths
        """
        crr = self.crr_values.get(road_type)
        if crr is None:
            return []
        
        # Extract emission classes from route file
        with open(route_file, 'r') as f:
            content = f.read()
        emission_classes = re.findall(r'emissionClass="([^\"]+)"', content)
        
        modified_files = []
        for emission_class in emission_classes:
            veh_path = self._get_vehicle_file_path(emission_class)
            if os.path.isfile(veh_path):
                self._backup_file(veh_path)
                self._modify_crr_value(veh_path, crr)
                modified_files.append(veh_path)
        
        return modified_files
    
    def restore_files(self, modified_files: List[str]):
        """Restore original vehicle files from backups."""
        for veh_path in set(modified_files):
            self._restore_file(veh_path)
    
    def _get_vehicle_file_path(self, emission_class: str) -> str:
        """Get full path to vehicle file."""
        return os.path.join(self.base_phem_dir, f"{emission_class}.PHEMLight.veh")
    
    def _backup_file(self, file_path: str):
        """Create backup of file if it doesn't exist."""
        backup_path = f"{file_path}.bak"
        if not os.path.exists(backup_path):
            shutil.copy2(file_path, backup_path)
    
    def _restore_file(self, file_path: str):
        """Restore file from backup."""
        backup_path = f"{file_path}.bak"
        if os.path.exists(backup_path):
            shutil.move(backup_path, file_path)
    
    def _modify_crr_value(self, veh_path: str, crr: float):
        """Modify CRR value in a vehicle file."""
        with open(veh_path, 'r') as f:
            lines = f.read().splitlines()
        
        new_lines = []
        skip_next = False
        
        for line in lines:
            if skip_next:
                skip_next = False
                continue
            
            if line.strip().lower() == 'c fr0':
                new_lines.append(line)
                new_lines.append(str(crr))
                skip_next = True
            else:
                new_lines.append(line)
        
        with open(veh_path, 'w') as f:
            f.write("\n".join(new_lines))
