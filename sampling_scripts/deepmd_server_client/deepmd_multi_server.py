#!/usr/bin/env python3
"""
Multi-Server DeepMD Manager
Starts multiple independent DeepMD servers on different ports
Each server has its own model instance, avoiding concurrency issues
"""

import os
import sys
import time
import signal
import subprocess
import argparse
from pathlib import Path

class DeepMDMultiServer:
    def __init__(self, model_file, num_servers=4, base_port=50001):
        self.model_file = model_file
        self.num_servers = num_servers
        self.base_port = base_port
        self.servers = []
        self.server_urls = []
        
        # Generate server URLs
        for i in range(num_servers):
            port = base_port + i
            self.server_urls.append(f"http://127.0.0.1:{port}")
    
    def start_servers(self):
        """Start all server instances"""
        print(f"Starting {self.num_servers} DeepMD servers...")
        
        for i in range(self.num_servers):
            port = self.base_port + i
            log_file = f"deepmd_server_{port}.log"
            
            # Create modified server script for this port
            server_script = self._create_server_script(port)
            
            # Start server process
            cmd = [sys.executable, server_script, self.model_file]
            process = subprocess.Popen(
                cmd,
                stdout=open(log_file, 'w'),
                stderr=subprocess.STDOUT,
                preexec_fn=os.setsid  # Create new process group
            )
            
            self.servers.append({
                'process': process,
                'port': port,
                'log_file': log_file,
                'script': server_script
            })
            
            print(f"  Server {i+1}: Port {port}, PID {process.pid}")
        
        # Wait for servers to start
        print("Waiting for servers to start...")
        time.sleep(5)
        
        # Verify all servers are running
        self._verify_servers()
    
    def _create_server_script(self, port):
        """Create a server script for specific port"""
        script_path = f"/tmp/deepmd_server_{port}.py"
        
        server_code = f'''#!/usr/bin/env python3
"""
Single DeepMD Server instance for port {port}
"""

import os
import sys
import json
import numpy as np
from flask import Flask, request, jsonify
from deepmd.calculator import DP
import ase.io
from ase import Atoms

app = Flask(__name__)
model = None

@app.route('/health', methods=['GET'])
def health():
    return jsonify({{"status": "ok", "model_loaded": model is not None, "port": {port}}})

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.json
        
        # Validate input data
        if data is None:
            raise ValueError("No JSON data received")
        
        if 'positions' not in data:
            raise ValueError("Missing 'positions' in request data")
        
        if 'symbols' not in data:
            raise ValueError("Missing 'symbols' in request data")
        
        # Reconstruct ASE Atoms object
        positions = np.array(data['positions'])
        symbols = data['symbols']
        cell = np.array(data['cell']) if data.get('cell') else None
        pbc = data.get('pbc', False)
        
        # Validate data shapes
        if len(positions.shape) != 2 or positions.shape[1] != 3:
            raise ValueError(f"Invalid positions shape: {{positions.shape}}, expected (N, 3)")
        
        if len(symbols) != len(positions):
            raise ValueError(f"Mismatch: {{len(symbols)}} symbols vs {{len(positions)}} positions")
        
        # Additional validation for symbols
        if symbols is None:
            raise ValueError("symbols is None")
        
        if not isinstance(symbols, list):
            raise ValueError(f"symbols must be a list, got {{type(symbols)}}")
        
        if any(s is None for s in symbols):
            raise ValueError("Some symbols are None")
        
        atoms = Atoms(symbols=symbols, positions=positions, cell=cell, pbc=pbc)
        
        if model is None:
            raise ValueError("Model is None")
        
        # Use the single model instance (no threading issues since each server is independent)
        atoms.calc = model
        
        # Calculate energy and forces
        energy = atoms.get_potential_energy()
        forces = atoms.get_forces()
        
        return jsonify({{
            "energy": energy,
            "forces": forces.tolist(),
            "status": "success",
            "server_port": {port}
        }})
    except Exception as e:
        import traceback
        error_msg = f"Server error: {{str(e)}}\\nTraceback: {{traceback.format_exc()}}"
        print(error_msg)  # Log to server console
        return jsonify({{
            "status": "error",
            "message": str(e),
            "traceback": traceback.format_exc(),
            "server_port": {port}
        }}), 500

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python deepmd_server.py model.pth")
        sys.exit(1)
    
    model_file = sys.argv[1]
    print(f"Loading model on port {port}: {{model_file}}")
    
    try:
        model = DP(model=model_file)
        print(f"Model loaded successfully on port {port}")
    except Exception as e:
        print(f"Error loading model on port {port}: {{e}}")
        sys.exit(1)
    
    # Run server (no threading needed since each server is independent)
    app.run(host='127.0.0.1', port={port}, debug=False, threaded=False)
'''
        
        with open(script_path, 'w') as f:
            f.write(server_code)
        
        # Make executable
        os.chmod(script_path, 0o755)
        return script_path
    
    def _verify_servers(self):
        """Verify all servers are running"""
        import requests
        
        running_count = 0
        for i, server in enumerate(self.servers):
            try:
                url = f"http://127.0.0.1:{server['port']}/health"
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    running_count += 1
                    print(f"  ✓ Server {i+1} (port {server['port']}) is running")
                else:
                    print(f"  ✗ Server {i+1} (port {server['port']}) health check failed")
            except Exception as e:
                print(f"  ✗ Server {i+1} (port {server['port']}) connection failed: {e}")
        
        print(f"\\nTotal: {running_count}/{self.num_servers} servers running")
        return running_count == self.num_servers
    
    def stop_servers(self):
        """Stop all server instances"""
        print("Stopping all servers...")
        
        for i, server in enumerate(self.servers):
            try:
                # Kill process group to ensure all child processes are terminated
                os.killpg(os.getpgid(server['process'].pid), signal.SIGTERM)
                server['process'].wait(timeout=5)
                print(f"  ✓ Server {i+1} (port {server['port']}) stopped")
            except Exception as e:
                print(f"  ! Server {i+1} (port {server['port']}) stop failed: {e}")
                try:
                    # Force kill if necessary
                    os.killpg(os.getpgid(server['process'].pid), signal.SIGKILL)
                except:
                    pass
            
            # Clean up temporary script
            try:
                os.remove(server['script'])
            except:
                pass
    
    def get_server_urls(self):
        """Get list of all server URLs"""
        return self.server_urls
    
    def get_status(self):
        """Get status of all servers"""
        import requests
        
        status = []
        for server in self.servers:
            try:
                url = f"http://127.0.0.1:{server['port']}/health"
                response = requests.get(url, timeout=2)
                if response.status_code == 200:
                    status.append({"port": server['port'], "status": "running"})
                else:
                    status.append({"port": server['port'], "status": "error"})
            except:
                status.append({"port": server['port'], "status": "down"})
        
        return status

def main():
    parser = argparse.ArgumentParser(description='DeepMD Multi-Server Manager')
    parser.add_argument('model_file', help='Path to DeepMD model file')
    parser.add_argument('--num-servers', type=int, default=4, help='Number of server instances')
    parser.add_argument('--base-port', type=int, default=50001, help='Base port number')
    parser.add_argument('--action', choices=['start', 'stop', 'status'], default='start')
    
    args = parser.parse_args()
    
    manager = DeepMDMultiServer(args.model_file, args.num_servers, args.base_port)
    
    if args.action == 'start':
        try:
            manager.start_servers()
            print(f"\\nAll servers started successfully!")
            print("Server URLs:")
            for url in manager.get_server_urls():
                print(f"  {url}")
            
            print(f"\\nPress Ctrl+C to stop all servers...")
            
            # Keep running until interrupted
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\\nReceived interrupt signal...")
        finally:
            manager.stop_servers()
    
    elif args.action == 'stop':
        # TODO: Implement stop existing servers
        print("Stop functionality not yet implemented")
    
    elif args.action == 'status':
        # TODO: Implement status check
        print("Status functionality not yet implemented")

if __name__ == '__main__':
    main() 