import socket
import re

class WakeOnLan:
    @staticmethod
    def send_magic_packet(mac_address: str, broadcast_ip: str = "255.255.255.255") -> bool:
        """
        Hedef MAC adresine UDP üzerinden Wake-on-LAN Magic Packet gönderir.
        """
        try:
            # MAC adresini temizle (sadece hex karakterleri bırak)
            mac_clean = re.sub(r'[^a-fA-F0-9]', '', mac_address)
            if len(mac_clean) != 12:
                raise ValueError("Geçersiz MAC adresi formatı. 12 haneli olmalıdır.")
            
            # Magic Packet Kuralları: 6 adet FF + 16 kez MAC adresi
            payload = bytes.fromhex('FF' * 6 + mac_clean * 16)
            
            # UDP Broadcast Soketi oluştur
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                # Genelde WoL için Port 9 veya 7 kullanılır
                sock.sendto(payload, (broadcast_ip, 9))
                
            return True
        except Exception as e:
            raise Exception(f"WoL Paketi Gönderilemedi: {str(e)}")