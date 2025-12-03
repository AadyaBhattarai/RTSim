"""Network generation utilities for SUMO simulations."""
import re
import subprocess
import os
from typing import List, Tuple

class NetworkGenerator:
    """Handles SUMO network generation from OpenDRIVE files."""
    
    def __init__(self, input_file: str, base_output: str):
        self.input_file = input_file
        self.base_output = base_output
    
    def generate_networks(self, slopes: List[float]) -> List[Tuple[float, str]]:
        """
        Generate SUMO network files for different slope values.
        
        Args:
            slopes: List of slope values to generate networks for
            
        Returns:
            List of tuples (slope_value, network_file_path)
        """
        networks = []
        for slope in slopes:
            output_path = f"{self.base_output}_slope_{slope}.net.xml"
            self._generate_single_network(slope, output_path)
            networks.append((slope, output_path))
        return networks
    
    def _generate_single_network(self, slope: float, output_path: str):
        """Generate a single network file with specified slope."""
        with open(self.input_file, 'r') as f:
            data = f.read()
        
        # Replace slope value in OpenDRIVE file
        data = re.sub(r'b=".*?"', f'b="{slope}"', data)
        
        # Write temporary file
        temp_file = "temp.xodr"
        with open(temp_file, 'w') as f:
            f.write(data)
        
        # Convert to SUMO network
        subprocess.run(
            f"netconvert --opendrive-files {temp_file} --ignore-errors -o {output_path}",
            shell=True,
            check=True
        )
        
        # Cleanup
        os.remove(temp_file)
