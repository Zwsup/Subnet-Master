import platform
import subprocess
import ipaddress
import socket
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

class NetworkScanner:
    @staticmethod
    def get_my_local_network() -> str:
        """Sistemin şu anda internete çıktığı aktif IP'yi ve Subnet'i otomatik tespit eder."""
        try:
            # 1. Aktif IP'yi bulmak için dışarıya sahte bir UDP paketi atıyoruz
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                my_ip = s.getsockname()[0]
                
            # 2. Subnet Mask'ı bulmak için ARP veya IPConfig (Windows) çıktısını okuyoruz
            out = subprocess.check_output("ipconfig", encoding="utf-8", errors="ignore")
            lines = out.split('\n')
            mask = "255.255.255.0" # Varsayılan fallback
            
            for i, line in enumerate(lines):
                if my_ip in line:
                    # IP'nin bulunduğu satırdan sonraki 1-3 satır içinde Subnet Mask yazar
                    for j in range(1, 4):
                        if i+j < len(lines) and ("Mask" in lines[i+j] or "Alt" in lines[i+j]):
                            match = re.search(r"(\d+\.\d+\.\d+\.\d+)", lines[i+j])
                            if match:
                                mask = match.group(1)
                                break
                    break
                    
            net = ipaddress.IPv4Network(f"{my_ip}/{mask}", strict=False)
            return str(net)
        except Exception:
            return "" # Tespit edilemezse boş döner

    # --- Aşağıdaki eski _ping_ip ve scan_network fonksiyonların aynı kalacak ---
    @staticmethod
    def _ping_ip(ip: str, timeout: int = 1) -> dict:
        # Mevcut kod...
        system_platform = platform.system().lower()
        if system_platform == "windows":
            cmd = ["ping", "-n", "1", "-w", str(timeout * 1000), ip]
            creationflags = subprocess.CREATE_NO_WINDOW
        else:
            cmd = ["ping", "-c", "1", "-W", str(timeout), ip]
            creationflags = 0
        try:
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=creationflags)
            return {"ip": ip, "status": "UP" if result.returncode == 0 else "DOWN"}
        except Exception:
            return {"ip": ip, "status": "ERROR"}

    @classmethod
    def scan_network(cls, cidr: str, max_threads: int = 50, progress_callback=None) -> list[dict]:
        # Mevcut kod...
        try:
            net = ipaddress.ip_network(cidr, strict=False)
            hosts = [str(ip) for ip in net.hosts()] if net.prefixlen <= 30 else [str(ip) for ip in net]
            if len(hosts) > 1024: raise ValueError("Ağ çok büyük!")
        except Exception as e:
            raise e

        results, completed = [], 0
        with ThreadPoolExecutor(max_workers=max_threads) as executor:
            future_to_ip = {executor.submit(cls._ping_ip, ip): ip for ip in hosts}
            for future in as_completed(future_to_ip):
                results.append(future.result())
                completed += 1
                if progress_callback: progress_callback(completed, len(hosts))

        results.sort(key=lambda x: ipaddress.ip_address(x["ip"]))
        return results