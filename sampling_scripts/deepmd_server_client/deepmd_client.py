#!/usr/bin/env python3
"""
DeepMD Client Calculator for ASE
Supports multiple DeepMD servers for load balancing and high performance
"""

import requests
import numpy as np
import time
import random
from ase.calculators.calculator import Calculator, all_changes

class DeepMDClient(Calculator):
    """ASE calculator that uses multiple DeepMD servers for calculations"""
    
    implemented_properties = ['energy', 'forces']
    
    def __init__(self, server_urls=None, max_retries=3, retry_delay=0.1, **kwargs):
        Calculator.__init__(self, **kwargs)
        
        # Support both single server and multi-server modes
        if server_urls is None:
            # Default single server
            self.server_urls = ['http://127.0.0.1:50001']
        elif isinstance(server_urls, str):
            # Single server URL
            self.server_urls = [server_urls]
        elif isinstance(server_urls, list):
            # Multiple server URLs
            self.server_urls = server_urls
        else:
            raise ValueError("server_urls must be a string or list of strings")
        
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.server_status = {}  # Track server health
        
        # Check if servers are running
        self._check_server_health()
    
    def _check_server_health(self):
        """Check health of all servers"""
        healthy_count = 0
        for url in self.server_urls:
            try:
                response = requests.get(f"{url}/health", timeout=5)
                if response.status_code == 200:
                    self.server_status[url] = True
                    healthy_count += 1
                else:
                    self.server_status[url] = False
                    print(f"Warning: Server {url} health check failed")
            except requests.exceptions.RequestException:
                self.server_status[url] = False
                print(f"Warning: Cannot connect to server {url}")
        
        if healthy_count == 0:
            raise RuntimeError(f"No healthy DeepMD servers found. Checked: {self.server_urls}")
        
        print(f"DeepMD Client: {healthy_count}/{len(self.server_urls)} servers available")
    
    def _get_available_server(self):
        """Get a healthy server URL with load balancing"""
        healthy_servers = [url for url, status in self.server_status.items() if status]
        
        if not healthy_servers:
            # Re-check server health
            self._check_server_health()
            healthy_servers = [url for url, status in self.server_status.items() if status]
            
            if not healthy_servers:
                raise RuntimeError("No healthy servers available")
        
        # Simple round-robin or random selection
        return random.choice(healthy_servers)
    
    def calculate(self, atoms=None, properties=['energy', 'forces'], 
                 system_changes=all_changes):
        """Calculate energy and forces via server with load balancing"""
        Calculator.calculate(self, atoms, properties, system_changes)
        
        # Critical check: ensure atoms is not None
        if atoms is None:
            raise ValueError("DeepMDClient.calculate: atoms object is None")
        
        # Additional safety checks for atoms object
        try:
            symbols = atoms.get_chemical_symbols()
            positions = atoms.get_positions()
        except Exception as e:
            raise ValueError(f"DeepMDClient.calculate: invalid atoms object: {e}")
        
        # Prepare data for server
        data = {
            'positions': positions.tolist(),
            'symbols': symbols,
            'cell': atoms.get_cell().tolist() if atoms.cell is not None else None,
            'pbc': atoms.get_pbc().tolist() if hasattr(atoms, 'pbc') else False
        }
        
        # Retry mechanism with server switching
        last_exception = None
        current_retry_delay = self.retry_delay
        
        for attempt in range(self.max_retries):
            try:
                # Get an available server
                server_url = self._get_available_server()
                
                # Send request to server
                response = requests.post(f"{server_url}/predict", json=data, timeout=30)
                
                if response.status_code != 200:
                    raise RuntimeError(f"Server HTTP error {response.status_code}: {response.text}")
                
                result = response.json()
                
                if result['status'] != 'success':
                    raise RuntimeError(f"Server calculation failed: {result.get('message', 'Unknown error')}")
                
                # Store results
                self.results['energy'] = result['energy']
                self.results['forces'] = np.array(result['forces']) 
                
                # Optional: print which server was used (for debugging)
                if 'server_port' in result:
                    pass  # print(f"[DEBUG] Used server port: {result['server_port']}")
                
                return  # Success, exit retry loop
                
            except Exception as e:
                last_exception = e
                
                # Mark server as unhealthy if it failed
                if 'server_url' in locals():
                    self.server_status[server_url] = False
                
                if attempt < self.max_retries - 1:  # Not the last attempt
                    print(f"DeepMD calculation attempt {attempt + 1} failed: {e}")
                    print(f"Retrying after {current_retry_delay:.1f} seconds...")
                    time.sleep(current_retry_delay)
                    # Exponential backoff
                    current_retry_delay *= 1.5
                else:
                    # Last attempt failed, re-raise the exception
                    raise last_exception

# Convenience function to create multi-server client
def create_multi_server_client(num_servers=4, base_port=50001):
    """Create a DeepMDClient that connects to multiple servers"""
    server_urls = [f"http://127.0.0.1:{base_port + i}" for i in range(num_servers)]
    return DeepMDClient(server_urls=server_urls) 