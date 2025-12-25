import sys
import os
import time
import socket
import struct
import ctypes
import logging
from datetime import datetime, timezone

# Constants
EPOCH_ADJUSTMENT = 2208988800  # 1970 - 1900 in seconds

# Configure logging
logging.basicConfig(
    filename='last_run.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class TimeFix:
    def __init__(self):
        self.config = {
            'NTPServer': 'pool.ntp.org',
            'DNSServer': None,
            'RetryDelay': 5,
            'MaxRetries': 0,
            'TimeZone': 'Bangladesh Standard Time'
        }
        self.load_config()

    def load_config(self):
        if getattr(sys, 'frozen', False):
            # If frozen with PyInstaller, executable is here
            base_path = os.path.dirname(sys.executable)
        else:
            # If running as script
            base_path = os.path.dirname(os.path.abspath(__file__))
            
        config_path = os.path.join(base_path, 'config.txt')
        if not os.path.exists(config_path):
            logging.warning(f"Config file not found at {config_path}. Using defaults.")
            return

        try:
            with open(config_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        if key in self.config:
                            if key == 'MaxRetries' or key == 'RetryDelay':
                                self.config[key] = int(value)
                            else:
                                self.config[key] = value if value else None
            logging.info(f"Loaded config: {self.config}")
        except Exception as e:
            logging.error(f"Error loading config: {e}")

    def resolve_hostname(self, hostname, dns_server=None):
        """Resolves hostname to IP, optionally using a specific DNS server."""
        # If it's already an IP, return it
        try:
            socket.inet_aton(hostname)
            return hostname
        except socket.error:
            pass

        if not dns_server:
            try:
                return socket.gethostbyname(hostname)
            except socket.gaierror:
                return None

        # Use nslookup for custom DNS
        try:
            # Run nslookup hostname dns_server
            import subprocess
            cmd = ['nslookup', hostname, dns_server]
            # prevent window popping up
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            result = subprocess.run(cmd, capture_output=True, text=True, startupinfo=startupinfo)
            if result.returncode != 0:
                logging.error(f"nslookup failed with return code {result.returncode}")
                return None
            
            # Parse output. 
            # Output format varies, but usually:
            # Server:  dns.google
            # Address:  8.8.8.8
            #
            # Non-authoritative answer:
            # Name:    pool.ntp.org
            # Addresses:  162.159.200.123
            #          162.159.200.1
            
            lines = result.stdout.splitlines()
            addresses = []
            capture = False
            for line in lines:
                line = line.strip()
                if line.startswith("Name:"):
                    capture = True
                elif capture and (line.startswith("Address:") or line.startswith("Addresses:")):
                    parts = line.split()
                    if len(parts) >= 2:
                        return parts[-1] # Return the first found address
                elif capture and line and not line.startswith("Aliases:"):
                     # Sometimes just an IP on a line
                     try:
                         # verify if it looks like an IP
                         if line.count('.') == 3:
                            return line
                     except:
                         pass

            logging.warning("nslookup ran but could not parse IP.")
            return None

        except Exception as e:
            logging.error(f"Error checking DNS: {e}")
            return None

    def get_ntp_time(self):
        """Fetches time from NTP server."""
        ntp_host = self.config['NTPServer']
        dns_server = self.config.get('DNSServer')
        
        ip_address = self.resolve_hostname(ntp_host, dns_server)
        if not ip_address:
            raise Exception(f"Could not resolve {ntp_host} using DNS {dns_server if dns_server else 'System'}")

        logging.info(f"Resolved {ntp_host} to {ip_address}")

        # Create socket
        client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client.settimeout(5)

        try:
            addr = (ip_address, 123)

            msg = b'\x1b' + 47 * b'\0'
            
            client.sendto(msg, addr)
            msg, address = client.recvfrom(1024)
            
            t = struct.unpack('!12I', msg)[10]
            t -= EPOCH_ADJUSTMENT
            return t
        finally:
            client.close()

    def set_system_time(self, timestamp):
        """Sets the system time. Requires Admin privileges."""
        try:
            # Convert timestamp to UTC structure
            # Windows SYSTEMTIME structure expects UTC
            
            utc_time = datetime.fromtimestamp(timestamp, timezone.utc)
            
            class SYSTEMTIME(ctypes.Structure):
                _fields_ = [
                    ("wYear", ctypes.c_ushort),
                    ("wMonth", ctypes.c_ushort),
                    ("wDayOfWeek", ctypes.c_ushort),
                    ("wDay", ctypes.c_ushort),
                    ("wHour", ctypes.c_ushort),
                    ("wMinute", ctypes.c_ushort),
                    ("wSecond", ctypes.c_ushort),
                    ("wMilliseconds", ctypes.c_ushort),
                ]

            st = SYSTEMTIME()
            st.wYear = utc_time.year
            st.wMonth = utc_time.month
            st.wDay = utc_time.day
            st.wHour = utc_time.hour
            st.wMinute = utc_time.minute
            st.wSecond = utc_time.second
            st.wMilliseconds = int(utc_time.microsecond / 1000)

            # Requires Admin
            ret = ctypes.windll.kernel32.SetSystemTime(ctypes.byref(st))
            if ret == 0:
                # Failed, usually permissions
                err = ctypes.GetLastError()
                logging.error(f"Failed to set system time. Error code: {err}. Are you running as Admin?")
                print(f"Failed to set system time. Error code: {err}")
                return False
            
            logging.info(f"System time set to: {utc_time} UTC")
            return True

        except Exception as e:
            logging.error(f"Error setting system time: {e}")
            return False

    def is_admin(self):
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False

    def set_timezone(self):
        """Sets the system timezone."""
        tz_id = self.config.get('TimeZone')
        if not tz_id:
            return

        try:
            # Check current timezone to avoid redundant calls
            # tzutil /g returns current timezone ID
            import subprocess
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            check_result = subprocess.run(['tzutil', '/g'], capture_output=True, text=True, startupinfo=startupinfo)
            if check_result.returncode == 0:
                current_tz = check_result.stdout.strip()
                if current_tz.lower() == tz_id.lower():
                    logging.info(f"Timezone is already set to {tz_id}. Skipping.")
                    return

            logging.info(f"Setting timezone to: {tz_id}")
            result = subprocess.run(['tzutil', '/s', tz_id], capture_output=True, text=True, startupinfo=startupinfo)
            if result.returncode == 0:
                logging.info("Timezone set successfully.")
            else:
                logging.error(f"Failed to set timezone: {result.stderr}")

        except Exception as e:
            logging.error(f"Error setting timezone: {e}")

    def run(self):
        if not self.is_admin():
            logging.error("Not running as admin. Cannot set time.")
            print("Error: This tool requires Administrator privileges to set the time.")
            # Depending on how it's launched, we might want to elevate. 
            # But the requirement says "The exe will be granted highest admin privileges in Task Scheduler", 
            # so we assume it starts as admin.
            return

        logging.info("TimeFix started.")
        
        # Set timezone first
        self.set_timezone()

        retries = 0
        max_retries = self.config['MaxRetries']
        
        while True:
            try:
                logging.info(f"Attempting time sync (Attempt {retries + 1})...")
                timestamp = self.get_ntp_time()
                if timestamp:
                    if self.set_system_time(timestamp):
                        logging.info("Time sync successful. Exiting.")
                        break
                
            except Exception as e:
                logging.error(f"Sync failed: {e}")
            
            if max_retries > 0 and retries >= max_retries:
                logging.error("Max retries reached. Exiting.")
                break
            
            retries += 1
            time.sleep(self.config['RetryDelay'])

if __name__ == '__main__':
    app = TimeFix()
    app.run()
