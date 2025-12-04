"""
Network generation utilities for creating SUMO networks from OpenDRIVE files.
"""

import os
import re
import subprocess
from typing import List, Tuple, Optional


class NetworkGenerator:
    """
    Generates SUMO network files from OpenDRIVE (.xodr) files.
    
    Supports generating multiple networks with different slope values
    for studying the effect of road grade on vehicle performance.
    """
    
    def __init__(self, output_dir: str = "data/sumo/networks"):
        """
        Initialize the network generator.
        
        Args:
            output_dir: Directory to store generated network files
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
    def generate_networks(
        self,
        input_file: str,
        base_output: str,
        slopes: List[float]
    ) -> List[Tuple[float, str]]:
        """
        Generate SUMO network files for multiple slope values.
        
        Args:
            input_file: Path to the input OpenDRIVE file
            base_output: Base name for output network files
            slopes: List of slope values to generate networks for
            
        Returns:
            List of tuples containing (slope_value, network_file_path)
        """
        networks = []
        
        for slope in slopes:
            network_file = self._generate_single_network(
                input_file, base_output, slope
            )
            if network_file:
                networks.append((slope, network_file))
                
        return networks
    
    def _generate_single_network(
        self,
        input_file: str,
        base_output: str,
        slope: float
    ) -> Optional[str]:
        """
        Generate a single SUMO network file with specified slope.
        
        Args:
            input_file: Path to the input OpenDRIVE file
            base_output: Base name for the output file
            slope: Slope value for the road
            
        Returns:
            Path to the generated network file or None if generation failed
        """
        output_file = os.path.join(
            self.output_dir,
            f"{base_output}_slope_{slope}.net.xml"
        )
        
        try:
            # Read and modify the OpenDRIVE file
            with open(input_file, 'r') as f:
                data = f.read()
                
            # Update slope value in the OpenDRIVE file
            modified_data = re.sub(r'b=".*?"', f'b="{slope}"', data)
            
            # Write to temporary file
            temp_file = "temp_network.xodr"
            with open(temp_file, 'w') as f:
                f.write(modified_data)
                
            # Run netconvert to generate SUMO network
            cmd = [
                "netconvert",
                "--opendrive-files", temp_file,
                "--ignore-errors",
                "-o", output_file
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            # Clean up temporary file
            os.remove(temp_file)
            
            print(f"Generated network: {output_file}")
            return output_file
            
        except subprocess.CalledProcessError as e:
            print(f"Error generating network for slope {slope}: {e.stderr}")
            return None
        except Exception as e:
            print(f"Error generating network for slope {slope}: {e}")
            return None
            
    def generate_network_from_command(
        self,
        input_file: str,
        output_file: str,
        additional_options: Optional[List[str]] = None
    ) -> bool:
        """
        Generate a network file using custom netconvert options.
        
        Args:
            input_file: Path to the input file (OpenDRIVE or other supported format)
            output_file: Path for the output network file
            additional_options: Additional command-line options for netconvert
            
        Returns:
            True if generation was successful, False otherwise
        """
        cmd = ["netconvert"]
        
        # Determine input type based on file extension
        ext = os.path.splitext(input_file)[1].lower()
        if ext == '.xodr':
            cmd.extend(["--opendrive-files", input_file])
        elif ext == '.osm':
            cmd.extend(["--osm-files", input_file])
        else:
            cmd.extend(["--sumo-net-file", input_file])
            
        cmd.extend(["-o", output_file])
        
        if additional_options:
            cmd.extend(additional_options)
            
        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            print(f"Generated network: {output_file}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error generating network: {e.stderr}")
            return False
            
    def validate_network(self, network_file: str) -> bool:
        """
        Validate a SUMO network file.
        
        Args:
            network_file: Path to the network file to validate
            
        Returns:
            True if the network is valid, False otherwise
        """
        if not os.path.exists(network_file):
            print(f"Network file not found: {network_file}")
            return False
            
        try:
            # Use SUMO's network validation
            cmd = ["sumo", "--net-file", network_file, "--no-step-log", "--duration", "1"]
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            return True
        except subprocess.CalledProcessError:
            return False
            
    def list_generated_networks(self) -> List[str]:
        """
        List all generated network files in the output directory.
        
        Returns:
            List of paths to network files
        """
        networks = []
        for filename in os.listdir(self.output_dir):
            if filename.endswith('.net.xml'):
                networks.append(os.path.join(self.output_dir, filename))
        return sorted(networks)
    
    def clean_networks(self) -> None:
        """Remove all generated network files from the output directory."""
        for filename in os.listdir(self.output_dir):
            if filename.endswith('.net.xml'):
                os.remove(os.path.join(self.output_dir, filename))
        print(f"Cleaned network files from {self.output_dir}")
