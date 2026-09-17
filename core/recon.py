import socket
import subprocess
import platform
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

class SecurityRecon:
    # Popüler donanım üreticilerinin MAC Önek (OUI) Veritabanı
    MAC_VENDORS = {
        "00:0C:29": "VMware Virtual NIC",
        "00:50:56": "VMware ESXi",
        "00:1A:11": "Google Inc.",
        "00:1B:63": "Apple Inc.",
        "38:F9:D3": "Apple Inc.",
        "B8:27:EB": "Raspberry Pi Foundation",
        "DC:A6:32": "Raspberry Pi Foundation",
        "00:1E:F7": "Cisco Systems",
        "00:24:14": "Cisco Systems",
        "4C:5E:0C": "Routerboard / MikroTik",
        "E0:63:E5": "TP-Link",
        "08:00:27": "Oracle VirtualBox",
        "00:1D:60": "ASUSTek Computer",
        "30:9C:23": "Hikvision Digital"
    }

    # Kritik Kurumsal Portlar ve Servis İsimleri
    COMMON_PORTS = {
        21: "FTP (Dosya Transfer)",
        22: "SSH (Güvenli Kabuk - Linux/Router)",
        23: "Telnet (Şifresiz Terminal)",
        25: "SMTP (Mail Sunucusu)",
        53: "DNS (Alan Adı Servisi)",
        80: "HTTP (Web / Yönetim Arayüzü)",
        110: "POP3 (Mail)",
        139: "NetBIOS / SMB",
        161: "SNMP (Ağ İzleme / Telemetri)",
        443: "HTTPS (Güvenli Web)",
        445: "SMB / CIFS (Windows Dosya Paylaşımı)",
        3306: "MySQL Veritabanı",
        3389: "RDP (Windows Uzak Masaüstü)",
        5432: "PostgreSQL Veritabanı",
        8080: "HTTP Alt / Proxy"
    }

    @classmethod
    def get_mac_and_vendor(cls, ip: str) -> dict:
        """Sistemin ARP tablosundan IP'nin fiziksel (MAC) adresini ve marka üreticisini çeker."""
        sys_plat = platform.system().lower()
        mac_addr = "N/A"
        vendor = "Bilinmeyen / Yerel Cihaz"

        try:
            if sys_plat == "windows":
                cmd = ["arp", "-a", ip]
            else:
                cmd = ["arp", "-n", ip]

            out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL).decode("utf-8", errors="ignore")
            # MAC adresini eşleştiren Regex (. - veya : ayraçlı)
            match = re.search(r"([0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2}", out)
            if match:
                mac_addr = match.group(0).upper().replace("-", ":")
                prefix = mac_addr[:8]
                vendor = cls.MAC_VENDORS.get(prefix, "Genel Donanım Üreticisi / OEM")
        except Exception:
            pass

        return {"mac": mac_addr, "vendor": vendor}

    @classmethod
    def _scan_single_port(cls, ip: str, port: int, timeout: float = 0.5) -> dict:
        """Belirtilen tek bir TCP portunu test eder."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            try:
                res = s.connect_ex((ip, port))
                is_open = (res == 0)
                return {
                    "port": port,
                    "service": cls.COMMON_PORTS.get(port, "Bilinmeyen Servis"),
                    "status": "OPEN" if is_open else "CLOSED"
                }
            except Exception:
                return {"port": port, "service": "Error", "status": "CLOSED"}

    @classmethod
    def scan_target_deep(cls, ip: str, custom_ports: list[int] = None) -> dict:
        """
        Hedef IP için MAC/Vendor analizi ve asenkron çoklu port taraması gerçekleştirir.
        """
        ports_to_scan = custom_ports if custom_ports else list(cls.COMMON_PORTS.keys())
        open_ports = []
        closed_count = 0

        # ARP / MAC Bilgisini Al
        mac_info = cls.get_mac_and_vendor(ip)

        # Multi-Threaded Port Taraması
        with ThreadPoolExecutor(max_workers=20) as executor:
            future_to_port = {executor.submit(cls._scan_single_port, ip, port): port for port in ports_to_scan}
            for future in as_completed(future_to_port):
                res = future.result()
                if res["status"] == "OPEN":
                    open_ports.append(res)
                else:
                    closed_count += 1

        open_ports.sort(key=lambda x: x["port"])

        # Cihaz Tipi Tahmini (Fingerprinting)
        device_type = "Genel Ağ Cihazı / İstemci"
        open_port_num_list = [p["port"] for p in open_ports]

        if 3389 in open_port_num_list or 445 in open_port_num_list:
            device_type = "Windows Sunucu / Masaüstü Makinesi"
        elif 22 in open_port_num_list and 80 not in open_port_num_list:
            device_type = "Linux Sunucu / Ağ Yönlendiricisi"
        elif 80 in open_port_num_list or 443 in open_port_num_list:
            if "Hikvision" in mac_info["vendor"]:
                device_type = "IP Güvenlik Kamerası (CCTV)"
            else:
                device_type = "Web Sunucusu / Ağ Geçidi (Modem/Router)"

        return {
            "ip": ip,
            "mac": mac_info["mac"],
            "vendor": mac_info["vendor"],
            "device_guess": device_type,
            "open_ports": open_ports,
            "closed_count": closed_count,
            "total_scanned": len(ports_to_scan)
        }