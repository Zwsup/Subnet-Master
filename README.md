# 🌐 Subnet Master

Modern, sezgisel ve hızlı bir masaüstü ağ hesaplama ve yönetim aracı. **Subnet Master**, karmaşık alt ağ (subnetting) hesaplamalarını ve yerel ağ işlemlerini kolaylaştırmak amacıyla geliştirilmiştir.

---

## 🚀 Özellikler

- **IPv4 Alt Ağ Hesaplama (Subnet Calculator):** IP adresi ve CIDR/Subnet Mask değerlerine göre ağ adresi, yayın adresi (broadcast), kullanılabilir host aralığı ve toplam host sayısını anında hesaplar.
- **VLSM Desteği:** İhtiyaca göre değişken uzunluklu alt ağ maskeleme (VLSM) tasarımı.
- **Aktif Ağ Taraması (Network Scanner):** Yerel ağdaki aktif cihazları ve IP/MAC adreslerini tespit etme.
- **Wake-on-LAN (WoL):** Ağdaki cihazları uzaktan uyandırmak için sihirli paket (Magic Packet) gönderme desteği.
- **Modern Arayüz:** Sade, kullanıcı dostu ve hızlı yanıt veren masaüstü arayüzü.

---

## 🛠️ Teknolojiler

- **Dil:** Python 3.x
- **Arayüz:** CustomTkinter / Tkinter
- **Ağ Kütüphaneleri:** `ipaddress`, `socket`, `scapy` / `subprocess`

---

## 📦 Kurulum ve Çalıştırma

### Gereksinimler
Projeyi kaynak kodundan çalıştırmak için Python 3.10+ kurulu olmalıdır.

1. **Repoyu klonlayın:**
   ```bash
   git clone [https://github.com/Zwsup/Subnet-Master.git](https://github.com/Zwsup/Subnet-Master.git)
   cd REPO_ADIN


Gerekli bağımlılıkları yükleyin:
pip install -r requirements.txt

Uygulamayı başlatın:
python main.py
