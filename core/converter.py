import ipaddress

class NetworkConverter:
    @staticmethod
    def ip_to_binary(ip_str: str) -> str:
        """IP adresini '11000000.168.00000001.00000000' formatında ikiliğe çevirir."""
        try:
            octets = ip_str.split('.')
            return '.'.join(f"{int(octet):08b}" for octet in octets)
        except Exception:
            return "Geçersiz IP"

    @staticmethod
    def get_ip_class_and_type(ip_str: str) -> dict:
        """IP sınıfını (A, B, C...) ve Public/Private durumunu tespit eder."""
        try:
            ip_obj = ipaddress.ip_address(ip_str)
            first_octet = int(str(ip_obj).split('.')[0])
            
            if 1 <= first_octet <= 126:
                ip_class = "A Sınıfı"
            elif 127 <= first_octet <= 127:
                ip_class = "Loopback (127.x.x.x)"
            elif 128 <= first_octet <= 191:
                ip_class = "B Sınıfı"
            elif 192 <= first_octet <= 223:
                ip_class = "C Sınıfı"
            elif 224 <= first_octet <= 239:
                ip_class = "D Sınıfı (Multicast)"
            else:
                ip_class = "E Sınıfı (Deneysel)"

            return {
                "class": ip_class,
                "is_private": "Özel Ağ (Private)" if ip_obj.is_private else "Genel Ağ (Public/Global)",
                "is_loopback": ip_obj.is_loopback
            }
        except Exception:
            return {"class": "Bilinmiyor", "is_private": "Bilinmiyor"}