"""
Natural VPS - Kami Tunnel Service
Handles automatic Kami tunnel setup and management for public IP exposure
"""

import subprocess
import os
import json
import re
import logging
from typing import Optional, Tuple
import platform

logger = logging.getLogger(__name__)

class KamiTunnelService:
    """Manages Kami tunnel setup and public URL generation"""
    
    KAMI_BINARY_PATH = "/usr/local/bin/kami"  # Linux/Mac path
    KAMI_WINDOWS_PATH = "C:\\Program Files\\Kami\\kami.exe"  # Windows path
    
    @staticmethod
    def get_kami_path() -> Optional[str]:
        """Get the path to Kami binary based on OS"""
        system = platform.system()
        
        if system == "Windows":
            return KamiTunnelService.KAMI_WINDOWS_PATH if os.path.exists(KamiTunnelService.KAMI_WINDOWS_PATH) else None
        elif system in ["Linux", "Darwin"]:
            return KamiTunnelService.KAMI_BINARY_PATH if os.path.exists(KamiTunnelService.KAMI_BINARY_PATH) else None
        
        return None
    
    @staticmethod
    def is_kami_installed() -> bool:
        """Check if Kami tunnel is installed on the system"""
        kami_path = KamiTunnelService.get_kami_path()
        return kami_path is not None
    
    @staticmethod
    def install_kami() -> Tuple[bool, str]:
        """Attempt to install Kami tunnel"""
        try:
            system = platform.system()
            
            if system == "Linux":
                # Linux installation
                commands = [
                    "curl -L https://github.com/kamipublic/KamiTunnel/releases/latest/download/kami-linux-amd64 -o /tmp/kami",
                    "chmod +x /tmp/kami",
                    "sudo mv /tmp/kami /usr/local/bin/kami"
                ]
                for cmd in commands:
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
                    if result.returncode != 0:
                        return False, f"Installation failed: {result.stderr}"
                
                return True, "Kami tunnel installed successfully"
            
            elif system == "Darwin":  # macOS
                commands = [
                    "curl -L https://github.com/kamipublic/KamiTunnel/releases/latest/download/kami-darwin-amd64 -o /tmp/kami",
                    "chmod +x /tmp/kami",
                    "sudo mv /tmp/kami /usr/local/bin/kami"
                ]
                for cmd in commands:
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
                    if result.returncode != 0:
                        return False, f"Installation failed: {result.stderr}"
                
                return True, "Kami tunnel installed successfully"
            
            elif system == "Windows":
                # Windows installation - requires manual download for now
                return False, "Manual Kami installation required on Windows. Download from https://github.com/kamipublic/KamiTunnel/releases"
            
            return False, "Unsupported operating system"
        
        except Exception as e:
            logger.error(f"Kami installation failed: {str(e)}")
            return False, f"Installation error: {str(e)}"
    
    @staticmethod
    def start_tunnel(local_url: str, tunnel_name: str = "natural-vps") -> Tuple[bool, Optional[str], str]:
        """
        Start a Kami tunnel
        
        Args:
            local_url: Local URL to tunnel (e.g. http://localhost:6080)
            tunnel_name: Name for the tunnel
        
        Returns:
            (success, public_url, message)
        """
        try:
            kami_path = KamiTunnelService.get_kami_path()
            if not kami_path:
                success, msg = KamiTunnelService.install_kami()
                if not success:
                    return False, None, f"Kami not installed: {msg}"
                kami_path = KamiTunnelService.get_kami_path()
            
            # Start tunnel with JSON output
            cmd = f'{kami_path} tunnel --url {local_url}'
            
            process = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for tunnel to start and get URL
            import time
            time.sleep(3)  # Wait for tunnel to initialize
            
            # Read output to get public URL
            line = process.stdout.readline() if process.stdout else ""
            
            # Parse Kami URL from output (usually like "https://xxxx.kami.dev")
            kami_match = re.search(r'https://[a-z0-9\-]+\.kami\.dev', line)
            if kami_match:
                public_url = kami_match.group(0)
                return True, public_url, "Kami tunnel started successfully"
            
            return False, None, "Failed to parse tunnel URL from Kami output"
        
        except subprocess.TimeoutExpired:
            return False, None, "Kami tunnel startup timeout"
        except Exception as e:
            logger.error(f"Kami tunnel error: {str(e)}")
            return False, None, f"Tunnel error: {str(e)}"
    
    @staticmethod
    def extract_tunnel_info(kami_output: str) -> dict:
        """
        Extract tunnel information from Kami output
        
        Expected format:
        ```
        Tunnel running on: https://xxxx.kami.dev
        Public IP: 1.2.3.4
        ```
        """
        info = {
            'tunnel_url': None,
            'public_ip': None,
            'status': 'unknown'
        }
        
        # Extract tunnel URL
        url_match = re.search(r'(https://[a-z0-9\-]+\.kami\.dev)', kami_output)
        if url_match:
            info['tunnel_url'] = url_match.group(1)
        
        # Extract public IP
        ip_match = re.search(r'(?:Public IP|IP Address):\s*(\d+\.\d+\.\d+\.\d+)', kami_output)
        if ip_match:
            info['public_ip'] = ip_match.group(1)
        
        if info['tunnel_url']:
            info['status'] = 'active'
        
        return info


class PublicIPService:
    """Manages public IP detection and configuration"""
    
    @staticmethod
    def get_public_ip() -> Tuple[bool, Optional[str]]:
        """Detect machine's public IP address"""
        try:
            import requests
            
            # Try multiple services for redundancy
            services = [
                'https://api.ipify.org?format=json',
                'https://checkip.amazonaws.com',
                'https://ifconfig.me'
            ]
            
            for service in services:
                try:
                    if 'ipify' in service:
                        response = requests.get(service, timeout=5).json()
                        return True, response.get('ip')
                    else:
                        response = requests.get(service, timeout=5).text.strip()
                        return True, response
                except:
                    continue
            
            return False, None
        
        except Exception as e:
            logger.error(f"Public IP detection failed: {str(e)}")
            return False, None
    
    @staticmethod
    def configure_firewall_rule(port: int, proto: str = "tcp") -> Tuple[bool, str]:
        """
        Configure firewall to allow port
        
        Args:
            port: Port number
            proto: Protocol (tcp/udp)
        
        Returns:
            (success, message)
        """
        try:
            system = platform.system()
            
            if system == "Linux":
                # UFW firewall
                cmd = f"sudo ufw allow {port}/{proto}"
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    return True, f"Firewall rule added for port {port}"
                else:
                    return False, f"Firewall configuration failed: {result.stderr}"
            
            elif system == "Windows":
                # Windows Firewall
                cmd = f'netsh advfirewall firewall add rule name="Natural VPS {port}" dir=in action=allow protocol={proto} localport={port}'
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    return True, f"Firewall rule added for port {port}"
                else:
                    return False, f"Firewall configuration failed: {result.stderr}"
            
            else:
                return False, "Unsupported operating system for firewall configuration"
        
        except subprocess.TimeoutExpired:
            return False, "Firewall configuration timeout"
        except Exception as e:
            logger.error(f"Firewall config error: {str(e)}")
            return False, f"Error: {str(e)}"
