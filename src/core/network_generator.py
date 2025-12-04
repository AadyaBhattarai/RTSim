"""
Network generation from OpenDRIVE files.
"""

import os
import re
import subprocess
from typing import List, Tuple


class NetworkGenerator:
    """Generates SUMO networks from OpenDRIVE files."""
    
    def __init__(self, output_dir: str = "networks"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def generate_networks(
        self,
        input_file: str,
        base_output: str,
        slopes: List[float]
    ) -> List[Tuple[float, str]]:
        """
        Generate SUMO networks for different slope values.
        
        Args:
            input_file: Path to OpenDRIVE (.xodr) file
            base_output: Base name for output files
            slopes: List of slope values
            
        Returns:
            List of (slope, network_path) tuples
        """
        nets = []
        
        for slope in slopes:
            out_file = os.path.join(self.output_dir, f"{base_output}_slope_{slope}.net.xml")
            
            with open(input_file, 'r') as f:
                data = f.read()
            
            data = re.sub(r'b=".*?"', f'b="{slope}"', data)
            
            tmp = "temp.xodr"
            with open(tmp, 'w') as f:
                f.write(data)
            
            try:
                subprocess.run(
                    f"netconvert --opendrive-files {tmp} --ignore-errors -o {out_file}",
                    shell=True, check=True
                )
                nets.append((slope, out_file))
                print(f"Generated network: {out_file}")
            except subprocess.CalledProcessError as e:
                print(f"Error generating network for slope {slope}: {e}")
            finally:
                if os.path.exists(tmp):
                    os.remove(tmp)
        
        return nets
    
    def list_networks(self) -> List[str]:
        """List all generated network files."""
        return [os.path.join(self.output_dir, f) for f in os.listdir(self.output_dir) if f.endswith('.net.xml')]
    
    def clean(self) -> None:
        """Remove all generated network files."""
        for f in os.listdir(self.output_dir):
            if f.endswith('.net.xml'):
                os.remove(os.path.join(self.output_dir, f))
