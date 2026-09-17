import customtkinter as ctk
from tkinter import filedialog, messagebox
import json
import csv
import threading

# Core Modülleri (Klasör yapında core/ altında olmalılar)
from core.calculator import SubnetCalculator
from core.config_gen import ConfigGenerator
from core.converter import NetworkConverter
from core.scanner import NetworkScanner
from core.database import ProjectDatabase
from core.validator import NetworkValidator
from core.summarizer import NetworkSummarizer
from core.recon import SecurityRecon
from core.wol import WakeOnLan  # Sadece WoL eklendi, SNMP çıkarıldı

# --- SMOOTH TASARIM PALETİ (FLUID UI) ---
THEME = {
    "bg_main": "#0F1115",
    "bg_surface": "#161920",
    "bg_card": "#1E212B",
    "bg_input": "#252936",
    "accent_blue": "#6366F1",
    "accent_blue_hover": "#4F46E5",
    "accent_cyan": "#0EA5E9",
    "accent_green": "#10B981",
    "accent_amber": "#F59E0B",
    "accent_red": "#F43F5E",
    "text_primary": "#F8FAFC",
    "text_muted": "#94A3B8",
    "border_color": "#2A2E3B"
}

ctk.set_appearance_mode("Dark")

class SubnetMasterApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("SubnetMaster v5.0 — Enterprise Cyber Studio")
        self.geometry("1020x880")
        self.configure(fg_color=THEME["bg_main"])
        self.resizable(False, False)

        # Veritabanı motoru
        self.db = ProjectDatabase()

        # 1. HEADER
        self._build_header()

        # 2. TABVIEW (9 SEKME)
        self.tabview = ctk.CTkTabview(
            self,
            width=960,
            height=760,
            fg_color=THEME["bg_surface"],
            segmented_button_fg_color=THEME["bg_card"],
            segmented_button_selected_color=THEME["accent_blue"],
            segmented_button_selected_hover_color=THEME["accent_blue_hover"],
            corner_radius=16
        )
        self.tabview.pack(padx=25, pady=(5, 15))

        self.tab_calc = self.tabview.add(" ⚡ Subnet ")
        self.tab_vlsm = self.tabview.add(" 📐 VLSM ")
        self.tab_scanner = self.tabview.add(" 🔍 Canlı Tarama ")
        self.tab_recon = self.tabview.add(" 🛡️ Keşif ")
        self.tab_validator = self.tabview.add(" 🚨 Denetim ")
        self.tab_summarizer = self.tabview.add(" 🖩 Supernetting ")
        self.tab_projects = self.tabview.add(" 🗄️ Projeler ")
        self.tab_config = self.tabview.add(" ⚙️ CLI Config ")
        self.tab_device = self.tabview.add(" 🔌 WoL (Cihaz Yön.) ")

        # Durum Değişkenleri
        self.last_calc_data = None
        self.last_vlsm_data = None
        self.is_scanning = False
        self.is_recoing = False

        # Sekmeleri İnşa Et
        self._build_calculator_tab()
        self._build_vlsm_tab()
        self._build_scanner_tab()
        self._build_recon_tab()
        self._build_validator_tab()
        self._build_summarizer_tab()
        self._build_projects_tab()
        self._build_config_tab()
        self._build_device_tab()

    def _build_header(self):
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=25, pady=(20, 5))
        
        title_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_box.pack(side="left")

        lbl_title = ctk.CTkLabel(
            title_box,
            text="SubnetMaster",
            font=ctk.CTkFont(family="Segoe UI", size=28, weight="bold"),
            text_color=THEME["text_primary"]
        )
        lbl_title.pack(side="left")
        
        lbl_badge = ctk.CTkLabel(
            title_box,
            text=" CYBER STUDIO ",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=THEME["accent_blue"],
            text_color="white",
            corner_radius=8
        )
        lbl_badge.pack(side="left", padx=(10, 0), pady=(4, 0))

        lbl_status = ctk.CTkLabel(
            header_frame,
            text="Desktop-Native Advanced Networking & Recon",
            font=ctk.CTkFont(size=13),
            text_color=THEME["text_muted"]
        )
        lbl_status.pack(side="right", pady=(8, 0))

    # ==========================================
    # --- TAB 1: HIZLI SUBNET ---
    # ==========================================
    def _build_calculator_tab(self):
        frame = self.tab_calc

        card_input = ctk.CTkFrame(frame, fg_color=THEME["bg_card"], corner_radius=16)
        card_input.pack(fill="x", padx=20, pady=(15, 10))

        lbl_ip = ctk.CTkLabel(card_input, text="IP ADRESİ VE PREFIX (CIDR)", font=ctk.CTkFont(size=11, weight="bold"), text_color=THEME["accent_cyan"])
        lbl_ip.pack(anchor="w", padx=20, pady=(15, 4))

        entry_frame = ctk.CTkFrame(card_input, fg_color="transparent")
        entry_frame.pack(fill="x", padx=20, pady=(0, 15))

        self.entry_ip = ctk.CTkEntry(
            entry_frame, placeholder_text="Örn: 192.168.1.0/24",
            font=ctk.CTkFont(family="Consolas", size=15), height=45,
            fg_color=THEME["bg_input"], border_width=0, corner_radius=10
        )
        self.entry_ip.pack(side="left", fill="x", expand=True, padx=(0, 12))

        btn_calc = ctk.CTkButton(
            entry_frame, text="Hesapla", width=140, height=45,
            font=ctk.CTkFont(size=14, weight="bold"), fg_color=THEME["accent_blue"],
            hover_color=THEME["accent_blue_hover"], corner_radius=10, command=self._on_calculate
        )
        btn_calc.pack(side="right")

        self.stats_frame = ctk.CTkFrame(frame, fg_color="transparent")
        self.stats_frame.pack(fill="x", padx=15, pady=5)

        self.card_net = self._create_stat_card(self.stats_frame, "NETWORK ADRESİ", "-", THEME["accent_cyan"], 0)
        self.card_mask = self._create_stat_card(self.stats_frame, "SUBNET MASK", "-", THEME["accent_blue"], 1)
        self.card_hosts = self._create_stat_card(self.stats_frame, "KULLANILABİLİR IP", "-", THEME["accent_green"], 2)
        self.card_class = self._create_stat_card(self.stats_frame, "AĞ SINIFI / TİP", "-", THEME["accent_amber"], 3)

        self.txt_result = ctk.CTkTextbox(
            frame, height=280, font=ctk.CTkFont(family="Consolas", size=14),
            fg_color=THEME["bg_input"], text_color=THEME["text_primary"],
            border_width=0, corner_radius=12
        )
        self.txt_result.pack(fill="x", padx=20, pady=10)

        btn_copy = ctk.CTkButton(
            frame, text="📋 Sonucu Panoya Kopyala", height=40,
            fg_color=THEME["bg_card"], hover_color=THEME["bg_input"],
            text_color=THEME["text_primary"], corner_radius=10,
            command=lambda: self._copy_to_clipboard(self.txt_result.get("1.0", "end"))
        )
        btn_copy.pack(anchor="e", padx=20, pady=(0, 5))

    def _create_stat_card(self, parent, title, value, accent_color, col):
        card = ctk.CTkFrame(parent, fg_color=THEME["bg_card"], corner_radius=12)
        card.grid(row=0, column=col, padx=5, pady=5, sticky="ew")
        parent.grid_columnconfigure(col, weight=1)

        accent_bar = ctk.CTkFrame(card, height=4, fg_color=accent_color, corner_radius=0)
        accent_bar.pack(fill="x", side="top")

        lbl_t = ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=10, weight="bold"), text_color=THEME["text_muted"])
        lbl_t.pack(anchor="w", padx=15, pady=(12, 2))

        lbl_v = ctk.CTkLabel(card, text=value, font=ctk.CTkFont(family="Consolas", size=14, weight="bold"), text_color=THEME["text_primary"])
        lbl_v.pack(anchor="w", padx=15, pady=(0, 15))
        return lbl_v

    def _on_calculate(self):
        ip_val = self.entry_ip.get().strip()
        self.txt_result.delete("1.0", "end")
        try:
            res = SubnetCalculator.calculate_subnet(ip_val)
            self.last_calc_data = res
            self.card_net.configure(text=res['network_address'])
            self.card_mask.configure(text=res['netmask'])
            self.card_hosts.configure(text=f"{res['usable_hosts']:,}".replace(",", "."))
            self.card_class.configure(text=f"{res['ip_class'].split()[0]} | {'Private' if 'Özel' in res['ip_type'] else 'Public'}")

            output = (
                f" === [ AĞ TEMEL SPEKTRUMU ] ===\n"
                f"  • Network Adresi   : {res['network_address']}\n"
                f"  • Subnet Mask      : {res['netmask']}\n"
                f"  • Wildcard Mask    : {res['wildcard_mask']}\n"
                f"  • Broadcast IP     : {res['broadcast_address']}\n"
                f"  • Kullanılabilir   : {res['first_host']}  <-->  {res['last_host']}\n"
                f"  • Toplam Kapasite  : {res['total_hosts']} IP (Aktif Host: {res['usable_hosts']})\n\n"
                f" === [ SINIF VE GÜVENLİK ALANI ] ===\n"
                f"  • Sınıf Bilgisi    : {res['ip_class']}\n"
                f"  • Ağ Tipi          : {res['ip_type']}\n\n"
                f" === [ 32-BIT BINARY DÖNÜŞÜM ] ===\n"
                f"  • Network Binary   : {res['net_binary']}\n"
                f"  • Netmask Binary   : {res['mask_binary']}\n"
            )
            self.txt_result.insert("1.0", output)
        except Exception as e:
            self.txt_result.insert("1.0", f"[!] HATA: {str(e)}")

    # ==========================================
    # --- TAB 2: VLSM PLANLAYICI ---
    # ==========================================
    def _build_vlsm_tab(self):
        frame = self.tab_vlsm

        card_vlsm = ctk.CTkFrame(frame, fg_color=THEME["bg_card"], corner_radius=16)
        card_vlsm.pack(fill="x", padx=20, pady=(15, 10))

        top_row = ctk.CTkFrame(card_vlsm, fg_color="transparent")
        top_row.pack(fill="x", padx=20, pady=(15, 5))

        lbl_base = ctk.CTkLabel(top_row, text="ANA AĞ BLOĞU (ROOT CIDR):", font=ctk.CTkFont(size=11, weight="bold"), text_color=THEME["accent_cyan"])
        lbl_base.pack(side="left")

        self.entry_base_net = ctk.CTkEntry(
            top_row, placeholder_text="10.0.0.0/16", width=250, height=35,
            font=ctk.CTkFont(family="Consolas", size=14), fg_color=THEME["bg_input"], 
            border_width=0, corner_radius=8
        )
        self.entry_base_net.pack(side="right")

        lbl_reqs = ctk.CTkLabel(card_vlsm, text="ALT AĞ İHTİYAÇLARI (GrupAdı:HostSayısı):", font=ctk.CTkFont(size=11, weight="bold"), text_color=THEME["text_muted"])
        lbl_reqs.pack(anchor="w", padx=20, pady=(5, 2))

        self.txt_reqs = ctk.CTkTextbox(
            card_vlsm, height=75, font=ctk.CTkFont(family="Consolas", size=13),
            fg_color=THEME["bg_input"], border_width=0, corner_radius=10
        )
        self.txt_reqs.pack(fill="x", padx=20, pady=(0, 15))
        self.txt_reqs.insert("1.0", "Web_Servers:12\nDatabase_Cluster:5\nOffice_Clients:60\nSecurity_Cameras:15")

        btn_plan = ctk.CTkButton(
            card_vlsm, text="⚡ VLSM Ağ Dağılımını Optimize Et", height=45,
            font=ctk.CTkFont(size=14, weight="bold"), fg_color=THEME["accent_green"], 
            hover_color="#0D9668", corner_radius=10, command=self._on_plan
        )
        btn_plan.pack(fill="x", padx=20, pady=(0, 15))

        card_prog = ctk.CTkFrame(frame, fg_color=THEME["bg_card"], corner_radius=12)
        card_prog.pack(fill="x", padx=20, pady=5)

        lbl_p_title = ctk.CTkLabel(card_prog, text="ANA AĞ KAPASİTE TAHSİSİ", font=ctk.CTkFont(size=11, weight="bold"), text_color=THEME["text_muted"])
        lbl_p_title.pack(anchor="w", padx=20, pady=(10, 2))

        self.progress_bar = ctk.CTkProgressBar(card_prog, height=10, corner_radius=5, progress_color=THEME["accent_blue"], fg_color=THEME["bg_input"])
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", padx=20, pady=5)

        self.lbl_progress_val = ctk.CTkLabel(card_prog, text="%0.0 tahsis edildi (0 IP)", font=ctk.CTkFont(size=12), text_color=THEME["text_muted"])
        self.lbl_progress_val.pack(anchor="e", padx=20, pady=(0, 10))

        self.txt_vlsm_result = ctk.CTkTextbox(
            frame, height=160, font=ctk.CTkFont(family="Consolas", size=13),
            fg_color=THEME["bg_input"], text_color=THEME["text_primary"], border_width=0, corner_radius=12
        )
        self.txt_vlsm_result.pack(fill="x", padx=20, pady=10)

        export_frame = ctk.CTkFrame(frame, fg_color="transparent")
        export_frame.pack(fill="x", padx=20, pady=(0, 5))

        btn_txt = self._create_export_btn(export_frame, "📄 TXT", self._export_txt)
        btn_txt.pack(side="left", padx=(0, 8))

        btn_json = self._create_export_btn(export_frame, "{ } JSON", self._export_json)
        btn_json.pack(side="left", padx=8)

        btn_csv = self._create_export_btn(export_frame, "📊 CSV", self._export_csv)
        btn_csv.pack(side="left", padx=8)

        btn_db_save = ctk.CTkButton(
            export_frame, text="💾 Projeyi Veritabanına Kaydet", width=200, height=40,
            fg_color=THEME["accent_blue"], hover_color=THEME["accent_blue_hover"],
            font=ctk.CTkFont(size=13, weight="bold"), corner_radius=10, command=self._save_to_db
        )
        btn_db_save.pack(side="right")

    def _create_export_btn(self, parent, text, command):
        return ctk.CTkButton(
            parent, text=text, width=90, height=40,
            fg_color=THEME["bg_card"], hover_color=THEME["bg_input"],
            text_color=THEME["text_primary"], corner_radius=10, command=command
        )

    def _on_plan(self):
        base_net = self.entry_base_net.get().strip()
        raw_reqs = self.txt_reqs.get("1.0", "end").strip().split("\n")
        self.txt_vlsm_result.delete("1.0", "end")
        
        req_list = []
        for line in raw_reqs:
            if ":" in line:
                name, count = line.split(":")
                if count.strip().isdigit():
                    req_list.append({"name": name.strip(), "hosts": int(count.strip())})

        try:
            data = SubnetCalculator.calculate_vlsm(base_net, req_list)
            self.last_vlsm_data = data
            ratio = data["usage_ratio"]
            self.progress_bar.set(ratio)
            self.lbl_progress_val.configure(text=f"%{ratio * 100:.1f} kapasite tahsis edildi ({data['total_allocated']}/{data['total_capacity']} IP)")

            output = " === [ OPTİMİZE EDİLMİŞ VLSM ALT AĞ HARİTASI ] ===\n\n"
            for r in data["subnets"]:
                output += f" ▪ [{r['name']}]  -->  İhtiyaç: {r['requested_hosts']} Host\n"
                output += f"    • Atanan CIDR : {r['allocated_cidr']}\n"
                output += f"    • Subnet Mask : {r['netmask']}\n"
                output += f"    • IP Aralığı  : {r['usable_range']} (Kapasite: {r['total_usable']})\n\n"
            
            self.txt_vlsm_result.insert("1.0", output)
        except Exception as e:
            self.txt_vlsm_result.insert("1.0", f"[!] HATA: {str(e)}")

    def _save_to_db(self):
        if not self.last_vlsm_data:
            messagebox.showwarning("Uyarı", "Önce 'Optimize Et' butonuna basarak bir plan oluşturmalısınız.")
            return

        dialog = ctk.CTkInputDialog(text="Bu VLSM ağ planı için benzersiz bir proje adı girin:", title="Projeyi Kaydet")
        proj_name = dialog.get_input()
        
        if proj_name and proj_name.strip():
            try:
                base_net = self.entry_base_net.get().strip()
                self.db.save_project(proj_name.strip(), base_net, self.last_vlsm_data)
                messagebox.showinfo("Başarılı", f"'{proj_name.strip()}' başarıyla kaydedildi!")
                self._refresh_projects_list()
            except Exception as e:
                messagebox.showerror("Hata", f"Proje kaydedilirken bir hata oluştu: {str(e)}")

    # ==========================================
    # --- TAB 3: CANLI TARAYICI (SMOOTH & AUTO) ---
    # ==========================================
    def _build_scanner_tab(self):
        frame = self.tab_scanner

        card_scan = ctk.CTkFrame(frame, fg_color=THEME["bg_card"], corner_radius=16)
        card_scan.pack(fill="x", padx=20, pady=(15, 10))

        lbl_scan_info = ctk.CTkLabel(card_scan, text="HEDEF ALT AĞ (CIDR)", font=ctk.CTkFont(size=11, weight="bold"), text_color=THEME["accent_cyan"])
        lbl_scan_info.pack(anchor="w", padx=20, pady=(15, 0))

        scan_input_frame = ctk.CTkFrame(card_scan, fg_color="transparent")
        scan_input_frame.pack(fill="x", padx=20, pady=(5, 15))

        self.entry_scan_cidr = ctk.CTkEntry(
            scan_input_frame, placeholder_text="Örn: 192.168.1.0/24",
            font=ctk.CTkFont(family="Consolas", size=15), height=45,
            fg_color=THEME["bg_input"], border_width=0, corner_radius=10
        )
        self.entry_scan_cidr.pack(side="left", fill="x", expand=True, padx=(0, 10))

        btn_auto_detect = ctk.CTkButton(
            scan_input_frame, text="✨ Ağımı Bul", width=110, height=45,
            font=ctk.CTkFont(size=13, weight="bold"), fg_color=THEME["bg_input"],
            hover_color=THEME["border_color"], text_color=THEME["accent_cyan"],
            corner_radius=10, command=self._auto_detect_network
        )
        btn_auto_detect.pack(side="left", padx=(0, 10))

        self.btn_start_scan = ctk.CTkButton(
            scan_input_frame, text="🚀 Canlı Tarama Başlat", width=170, height=45,
            font=ctk.CTkFont(size=13, weight="bold"), fg_color=THEME["accent_blue"],
            hover_color=THEME["accent_blue_hover"], corner_radius=10, command=self._start_scan_thread
        )
        self.btn_start_scan.pack(side="right")

        card_prog_scan = ctk.CTkFrame(frame, fg_color=THEME["bg_card"], corner_radius=12)
        card_prog_scan.pack(fill="x", padx=20, pady=5)

        self.scan_progress_bar = ctk.CTkProgressBar(card_prog_scan, height=10, corner_radius=5, progress_color=THEME["accent_green"], fg_color=THEME["bg_input"])
        self.scan_progress_bar.set(0)
        self.scan_progress_bar.pack(fill="x", padx=20, pady=(15, 5))

        self.lbl_scan_status = ctk.CTkLabel(card_prog_scan, text="Tarama bekleniyor...", font=ctk.CTkFont(size=12), text_color=THEME["text_muted"])
        self.lbl_scan_status.pack(anchor="e", padx=20, pady=(0, 10))

        self.txt_scan_result = ctk.CTkTextbox(
            frame, height=280, font=ctk.CTkFont(family="Consolas", size=14),
            fg_color=THEME["bg_input"], text_color=THEME["text_primary"],
            border_width=0, corner_radius=12
        )
        self.txt_scan_result.pack(fill="x", padx=20, pady=10)

    def _auto_detect_network(self):
        detected_cidr = NetworkScanner.get_my_local_network()
        if detected_cidr:
            self.entry_scan_cidr.delete(0, "end")
            self.entry_scan_cidr.insert(0, detected_cidr)
        else:
            messagebox.showwarning("Hata", "Aktif yerel ağ tespit edilemedi.")

    def _start_scan_thread(self):
        if self.is_scanning: return
        cidr = self.entry_scan_cidr.get().strip()
        if not cidr: return

        self.is_scanning = True
        self.btn_start_scan.configure(text="⏳ Taranıyor...", state="disabled")
        self.txt_scan_result.delete("1.0", "end")
        self.txt_scan_result.insert("1.0", f"[*] {cidr} bloğu için ping taraması yapılıyor...\n")
        self.scan_progress_bar.set(0)

        threading.Thread(target=self._run_scan, args=(cidr,), daemon=True).start()

    def _run_scan(self, cidr):
        def on_progress(completed, total):
            ratio = completed / total
            self.scan_progress_bar.set(ratio)
            self.lbl_scan_status.configure(text=f"Tarama İlerliyor: %{ratio*100:.1f} ({completed}/{total})")

        try:
            results = NetworkScanner.scan_network(cidr, max_threads=60, progress_callback=on_progress)
            up_hosts = [r for r in results if r["status"] == "UP"]
            down_hosts = [r for r in results if r["status"] == "DOWN"]

            output = (
                f" === [ CANLI AĞ KEŞİF RAPORU ] ===\n"
                f" ▪ Taranan Host : {len(results)}  |  Aktif (UP) : {len(up_hosts)}  |  Kapalı : {len(down_hosts)}\n\n"
                f" [ ÇEVRİMİÇİ (UP) CİHAZ LİSTESİ ]\n"
            )
            if up_hosts:
                for h in up_hosts: output += f"  [+] {h['ip']} --> ONLINE\n"
            else:
                output += "  [-] Çevrimiçi cihaz bulunamadı.\n"

            self.txt_scan_result.delete("1.0", "end")
            self.txt_scan_result.insert("1.0", output)
            self.lbl_scan_status.configure(text=f"Tamamlandı! {len(up_hosts)} cihaz aktif.")
        except Exception as e:
            self.txt_scan_result.insert("end", f"\n[!] HATA: {str(e)}")
            self.lbl_scan_status.configure(text="Tarama başarısız.")
        finally:
            self.is_scanning = False
            self.btn_start_scan.configure(text="🚀 Canlı Tarama Başlat", state="normal")

    # ==========================================
    # --- TAB 4: RECON (GÜVENLİK KEŞFİ) ---
    # ==========================================
    def _build_recon_tab(self):
        frame = self.tab_recon

        card_recon = ctk.CTkFrame(frame, fg_color=THEME["bg_card"], corner_radius=16)
        card_recon.pack(fill="x", padx=20, pady=(15, 10))

        lbl_r = ctk.CTkLabel(card_recon, text="HEDEF TEKİL IP ADRESİ (Port & MAC)", font=ctk.CTkFont(size=11, weight="bold"), text_color=THEME["accent_red"])
        lbl_r.pack(anchor="w", padx=20, pady=(15, 4))

        recon_box = ctk.CTkFrame(card_recon, fg_color="transparent")
        recon_box.pack(fill="x", padx=20, pady=(0, 15))

        self.entry_recon_ip = ctk.CTkEntry(
            recon_box, placeholder_text="Örn: 192.168.1.1",
            font=ctk.CTkFont(family="Consolas", size=15), height=45,
            fg_color=THEME["bg_input"], border_width=0, corner_radius=10
        )
        self.entry_recon_ip.pack(side="left", fill="x", expand=True, padx=(0, 12))

        self.btn_start_recon = ctk.CTkButton(
            recon_box, text="🛡️ Derin Keşfi Başlat", width=190, height=45,
            font=ctk.CTkFont(size=14, weight="bold"), fg_color=THEME["accent_red"],
            hover_color="#E11D48", corner_radius=10, command=self._start_recon_thread
        )
        self.btn_start_recon.pack(side="right")

        self.txt_recon_result = ctk.CTkTextbox(
            frame, height=360, font=ctk.CTkFont(family="Consolas", size=14),
            fg_color=THEME["bg_input"], text_color=THEME["text_primary"],
            border_width=0, corner_radius=12
        )
        self.txt_recon_result.pack(fill="x", padx=20, pady=10)

    def _start_recon_thread(self):
        if self.is_recoing: return
        ip = self.entry_recon_ip.get().strip()
        if not ip: return

        self.is_recoing = True
        self.btn_start_recon.configure(text="⏳ Analiz Ediliyor...", state="disabled")
        self.txt_recon_result.delete("1.0", "end")
        self.txt_recon_result.insert("1.0", f"[*] {ip} için MAC, Üretici ve TCP Port analizi yapılıyor...\n")
        threading.Thread(target=self._run_recon, args=(ip,), daemon=True).start()

    def _run_recon(self, ip):
        try:
            res = SecurityRecon.scan_target_deep(ip)
            output = (
                f" === [ HEDEF SİSTEM PROFİLİ ] ===\n"
                f" ▪ IP Adresi     : {res['ip']}\n"
                f" ▪ MAC Adresi    : {res['mac']}\n"
                f" ▪ Üretici Firma : {res['vendor']}\n"
                f" ▪ Sistem Tipi   : {res['device_guess']}\n\n"
                f" [ AÇIK TCP PORTLARI & SERVİSLER ]\n"
            )
            if res["open_ports"]:
                for p in res["open_ports"]: output += f"  [+] PORT {p['port']:<5} (OPEN) -> {p['service']}\n"
            else:
                output += "  [-] Taranan tüm portlar KAPALI.\n"

            self.txt_recon_result.delete("1.0", "end")
            self.txt_recon_result.insert("1.0", output)
        except Exception as e:
            self.txt_recon_result.insert("end", f"\n[!] HATA: {str(e)}")
        finally:
            self.is_recoing = False
            self.btn_start_recon.configure(text="🛡️ Derin Keşfi Başlat", state="normal")

    # ==========================================
    # --- TAB 5: ÇAKIŞMA & DENETİM ---
    # ==========================================
    def _build_validator_tab(self):
        frame = self.tab_validator

        card_val = ctk.CTkFrame(frame, fg_color=THEME["bg_card"], corner_radius=16)
        card_val.pack(fill="x", padx=20, pady=(15, 10))

        lbl_val = ctk.CTkLabel(card_val, text="DENETLENECEK ALT AĞLAR (Her satıra bir CIDR):", font=ctk.CTkFont(size=11, weight="bold"), text_color=THEME["accent_amber"])
        lbl_val.pack(anchor="w", padx=20, pady=(15, 4))

        self.txt_val_input = ctk.CTkTextbox(
            card_val, height=100, font=ctk.CTkFont(family="Consolas", size=14),
            fg_color=THEME["bg_input"], border_width=0, corner_radius=10
        )
        self.txt_val_input.pack(fill="x", padx=20, pady=(0, 15))
        self.txt_val_input.insert("1.0", "10.0.1.0/24\n10.0.1.128/25\n192.168.1.0/24")

        btn_val = ctk.CTkButton(
            card_val, text="🛡️ Ağ Çakışmalarını (Overlap) Denetle", height=45,
            font=ctk.CTkFont(size=14, weight="bold"), fg_color=THEME["accent_amber"],
            hover_color="#D97706", corner_radius=10, command=self._on_validate_overlaps
        )
        btn_val.pack(fill="x", padx=20, pady=(0, 15))

        self.txt_val_result = ctk.CTkTextbox(
            frame, height=270, font=ctk.CTkFont(family="Consolas", size=14),
            fg_color=THEME["bg_input"], text_color=THEME["text_primary"], border_width=0, corner_radius=12
        )
        self.txt_val_result.pack(fill="x", padx=20, pady=10)

    def _on_validate_overlaps(self):
        raw_list = self.txt_val_input.get("1.0", "end").strip().split("\n")
        self.txt_val_result.delete("1.0", "end")
        res = NetworkValidator.analyze_overlaps(raw_list)

        output = " === [ MİMARİ DENETİM RAPORU ] ===\n\n"
        if res["overlaps"]:
            output += " 🔴 KRİTİK ALARM: KESİŞEN ALT AĞLAR BULUNDU!\n\n"
            for ov in res["overlaps"]:
                output += f"  ❌ {ov['network_a']} <--> {ov['network_b']}\n"
        else:
            output += " 🟢 HARİKA: Listedeki hiçbir ağ birbiriyle çakışmıyor.\n\n"

        self.txt_val_result.insert("1.0", output)

    # ==========================================
    # --- TAB 6: SUPERNETTING ---
    # ==========================================
    def _build_summarizer_tab(self):
        frame = self.tab_summarizer

        card_sum = ctk.CTkFrame(frame, fg_color=THEME["bg_card"], corner_radius=16)
        card_sum.pack(fill="x", padx=20, pady=(15, 10))

        lbl_sum = ctk.CTkLabel(card_sum, text="ÖZETLENECEK AĞLAR (Her satıra bir CIDR):", font=ctk.CTkFont(size=11, weight="bold"), text_color=THEME["accent_cyan"])
        lbl_sum.pack(anchor="w", padx=20, pady=(15, 4))

        self.txt_sum_input = ctk.CTkTextbox(
            card_sum, height=100, font=ctk.CTkFont(family="Consolas", size=14),
            fg_color=THEME["bg_input"], border_width=0, corner_radius=10
        )
        self.txt_sum_input.pack(fill="x", padx=20, pady=(0, 15))
        self.txt_sum_input.insert("1.0", "192.168.0.0/24\n192.168.1.0/24\n192.168.2.0/24\n192.168.3.0/24")

        btn_sum = ctk.CTkButton(
            card_sum, text="🖩 Supernet (Özet Rota) Hesapla", height=45,
            font=ctk.CTkFont(size=14, weight="bold"), fg_color=THEME["accent_blue"],
            hover_color=THEME["accent_blue_hover"], corner_radius=10, command=self._on_summarize
        )
        btn_sum.pack(fill="x", padx=20, pady=(0, 15))

        self.txt_sum_result = ctk.CTkTextbox(
            frame, height=270, font=ctk.CTkFont(family="Consolas", size=14),
            fg_color=THEME["bg_input"], text_color=THEME["text_primary"], border_width=0, corner_radius=12
        )
        self.txt_sum_result.pack(fill="x", padx=20, pady=10)

    def _on_summarize(self):
        raw_list = self.txt_sum_input.get("1.0", "end").strip().split("\n")
        self.txt_sum_result.delete("1.0", "end")
        res = NetworkSummarizer.summarize_networks(raw_list)

        if res.get("status") == "ERROR":
            self.txt_sum_result.insert("1.0", f"[!] HATA: {res['message']}")
            return
        
        output = (
            f" === [ SUPERNETTING RAPORU ] ===\n\n"
            f" ▪ ÖNERİLEN SUPERNET : {res['summary_cidr']}\n"
            f" ▪ Subnet Mask       : {res['summary_netmask']}\n\n"
            f" [ ROUTER KOMUTLARI ]\n"
            f" 🔹 Cisco:  {res['static_route_cisco']}\n"
            f" 🔹 MikroTik: {res['route_mikrotik']}\n"
        )
        self.txt_sum_result.insert("1.0", output)

    # ==========================================
    # --- TAB 7: KAYITLI PROJELER ---
    # ==========================================
    def _build_projects_tab(self):
        frame = self.tab_projects

        top_frame = ctk.CTkFrame(frame, fg_color="transparent")
        top_frame.pack(fill="x", padx=20, pady=(15, 10))

        lbl_info = ctk.CTkLabel(top_frame, text="🗄️ SQLite Yerel Ağ Projeleri", font=ctk.CTkFont(size=14, weight="bold"), text_color=THEME["text_primary"])
        lbl_info.pack(side="left")

        btn_refresh = ctk.CTkButton(
            top_frame, text="🔄 Yenile", width=100, height=35, 
            fg_color=THEME["bg_card"], hover_color=THEME["bg_input"], 
            corner_radius=8, command=self._refresh_projects_list
        )
        btn_refresh.pack(side="right")

        self.scroll_projects = ctk.CTkScrollableFrame(frame, width=900, height=500, fg_color=THEME["bg_card"], corner_radius=16)
        self.scroll_projects.pack(padx=20, pady=10, fill="both", expand=True)

        self._refresh_projects_list()

    def _refresh_projects_list(self):
        for child in self.scroll_projects.winfo_children():
            child.destroy()

        projects = self.db.get_all_projects()
        if not projects:
            lbl_empty = ctk.CTkLabel(self.scroll_projects, text="Henüz kaydedilmiş bir proje yok.", font=ctk.CTkFont(size=13), text_color=THEME["text_muted"])
            lbl_empty.pack(pady=40)
            return

        for p in projects:
            card = ctk.CTkFrame(self.scroll_projects, fg_color=THEME["bg_input"], corner_radius=12)
            card.pack(fill="x", padx=10, pady=8)

            info_box = ctk.CTkFrame(card, fg_color="transparent")
            info_box.pack(side="left", padx=20, pady=15)

            lbl_name = ctk.CTkLabel(info_box, text=p["name"], font=ctk.CTkFont(size=15, weight="bold"), text_color=THEME["accent_cyan"])
            lbl_name.pack(anchor="w")

            lbl_meta = ctk.CTkLabel(info_box, text=f"Ana Ağ: {p['base_network']}  |  Tarih: {p['created_at']}", font=ctk.CTkFont(size=12), text_color=THEME["text_muted"])
            lbl_meta.pack(anchor="w", pady=(4, 0))

            btn_box = ctk.CTkFrame(card, fg_color="transparent")
            btn_box.pack(side="right", padx=20, pady=15)

            btn_load = ctk.CTkButton(
                btn_box, text="📂 Yükle", width=100, height=35, 
                fg_color=THEME["accent_blue"], hover_color=THEME["accent_blue_hover"], 
                corner_radius=8, command=lambda name=p["name"]: self._load_project_to_ui(name)
            )
            btn_load.pack(side="left", padx=(0, 10))

            btn_delete = ctk.CTkButton(
                btn_box, text="🗑️ Sil", width=70, height=35, 
                fg_color=THEME["accent_red"], hover_color="#E11D48", 
                corner_radius=8, command=lambda name=p["name"]: self._delete_project_from_db(name)
            )
            btn_delete.pack(side="left")

    def _load_project_to_ui(self, proj_name: str):
        proj_data = self.db.get_project_by_name(proj_name)
        if not proj_data: return
        self.entry_base_net.delete(0, "end")
        self.entry_base_net.insert(0, proj_data["base_network"])

        subnets = proj_data["vlsm_data"].get("subnets", [])
        reqs_text = "\n".join(f"{s['name']}:{s['requested_hosts']}" for s in subnets)
        self.txt_reqs.delete("1.0", "end")
        self.txt_reqs.insert("1.0", reqs_text)
        self._on_plan()
        self.tabview.set(" 📐 VLSM ")

    def _delete_project_from_db(self, proj_name: str):
        if messagebox.askyesno("Onay", f"'{proj_name}' kalıcı olarak silinecek. Onaylıyor musun?"):
            self.db.delete_project(proj_name)
            self._refresh_projects_list()

    # ==========================================
    # --- TAB 8: CLI CONFIG ---
    # ==========================================
    def _build_config_tab(self):
        frame = self.tab_config

        card_cfg = ctk.CTkFrame(frame, fg_color=THEME["bg_card"], corner_radius=16)
        card_cfg.pack(fill="x", padx=20, pady=(15, 10))

        self.btn_gen_config = ctk.CTkButton(
            card_cfg, text="⚙️ VLSM Planı İçin CLI Komutlarını Üret", height=45, 
            font=ctk.CTkFont(size=14, weight="bold"), fg_color=THEME["accent_blue"], 
            hover_color=THEME["accent_blue_hover"], corner_radius=10, command=self._generate_cli_configs
        )
        self.btn_gen_config.pack(fill="x", padx=20, pady=20)

        self.txt_config_result = ctk.CTkTextbox(
            frame, height=380, font=ctk.CTkFont(family="Consolas", size=14),
            fg_color=THEME["bg_input"], text_color=THEME["text_primary"], border_width=0, corner_radius=12
        )
        self.txt_config_result.pack(fill="x", padx=20, pady=10)

        btn_copy_cfg = ctk.CTkButton(
            frame, text="📋 Tüm Konfigürasyonu Kopyala", height=40,
            fg_color=THEME["bg_card"], hover_color=THEME["bg_input"],
            text_color=THEME["text_primary"], corner_radius=10,
            command=lambda: self._copy_to_clipboard(self.txt_config_result.get("1.0", "end"))
        )
        btn_copy_cfg.pack(anchor="e", padx=20, pady=0)

    def _generate_cli_configs(self):
        self.txt_config_result.delete("1.0", "end")
        if not self.last_vlsm_data or "subnets" not in self.last_vlsm_data:
            self.txt_config_result.insert("1.0", "[!] Lütfen önce VLSM sekmesinde bir plan oluşturun.")
            return

        output = ""
        for index, sub in enumerate(self.last_vlsm_data["subnets"]):
            output += ConfigGenerator.generate_cisco(sub["name"], sub["gateway_ip"], sub["netmask"], f"GigabitEthernet0/{index+1}") + "\n"
            output += ConfigGenerator.generate_mikrotik(sub["name"], sub["gateway_ip"], sub["prefix"], f"ether{index+1}") + "\n"
            output += "# " + "=" * 60 + "\n\n"
        self.txt_config_result.insert("1.0", output)

    # ==========================================
    # --- TAB 9: CİHAZ YÖNETİMİ (SADECE WoL) ---
    # ==========================================
    def _build_device_tab(self):
        frame = self.tab_device

        card_wol = ctk.CTkFrame(frame, fg_color=THEME["bg_card"], corner_radius=16)
        card_wol.pack(fill="x", padx=20, pady=(15, 10))

        lbl_wol = ctk.CTkLabel(card_wol, text="🔌 WAKE-ON-LAN (Cihaz Uyandırma)", font=ctk.CTkFont(size=13, weight="bold"), text_color=THEME["accent_green"])
        lbl_wol.pack(anchor="w", padx=20, pady=(15, 5))

        wol_input_frame = ctk.CTkFrame(card_wol, fg_color="transparent")
        wol_input_frame.pack(fill="x", padx=20, pady=(0, 20))

        self.entry_wol_mac = ctk.CTkEntry(
            wol_input_frame, placeholder_text="Hedef MAC (Örn: 00:1A:2B:3C:4D:5E)",
            font=ctk.CTkFont(family="Consolas", size=14), height=45, width=280,
            fg_color=THEME["bg_input"], border_width=0, corner_radius=10
        )
        self.entry_wol_mac.pack(side="left", padx=(0, 10))

        self.entry_wol_ip = ctk.CTkEntry(
            wol_input_frame, placeholder_text="Broadcast IP (Örn: 192.168.1.255)",
            font=ctk.CTkFont(family="Consolas", size=14), height=45, width=220,
            fg_color=THEME["bg_input"], border_width=0, corner_radius=10
        )
        self.entry_wol_ip.pack(side="left", padx=(0, 10))

        btn_wol = ctk.CTkButton(
            wol_input_frame, text="🔮 Magic Packet Gönder", height=45,
            font=ctk.CTkFont(size=13, weight="bold"), fg_color=THEME["accent_green"],
            hover_color="#0D9668", corner_radius=10, command=self._on_send_wol
        )
        btn_wol.pack(side="right", fill="x", expand=True)

    def _on_send_wol(self):
        mac = self.entry_wol_mac.get().strip()
        b_ip = self.entry_wol_ip.get().strip() or "255.255.255.255"

        if not mac:
            messagebox.showwarning("Uyarı", "Uyandırılacak cihazın MAC adresini girmelisiniz.")
            return

        try:
            WakeOnLan.send_magic_packet(mac, b_ip)
            messagebox.showinfo("Başarılı", f"Sihirli paket {mac} adresine başarıyla fırlatıldı!\n(Cihazın BIOS'undan WoL ayarının açık olduğundan emin olun)")
        except Exception as e:
            messagebox.showerror("Hata", str(e))

    # ==========================================
    # --- YARDIMCI EXPORT & KOPYALAMA METOTLARI ---
    # ==========================================
    def _copy_to_clipboard(self, text: str):
        if not text.strip(): return
        self.clipboard_clear()
        self.clipboard_append(text.strip())
        messagebox.showinfo("Başarılı", "Panoya kopyalandı!")

    def _export_txt(self):
        if not self.last_vlsm_data:
            messagebox.showwarning("Uyarı", "Dışa aktarılacak bir ağ planı yok.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.txt_vlsm_result.get("1.0", "end"))
            messagebox.showinfo("Başarılı", "TXT raporu kaydedildi.")

    def _export_json(self):
        if not self.last_vlsm_data:
            messagebox.showwarning("Uyarı", "Dışa aktarılacak bir ağ planı yok.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
        if path:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.last_vlsm_data, f, ensure_ascii=False, indent=4)
            messagebox.showinfo("Başarılı", "JSON yapısı kaydedildi.")

    def _export_csv(self):
        if not self.last_vlsm_data:
            messagebox.showwarning("Uyarı", "Dışa aktarılacak bir ağ planı yok.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
        if path:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Grup Adı", "İstenen Host", "Atanan CIDR", "Netmask", "IP Aralığı"])
                for s in self.last_vlsm_data["subnets"]:
                    writer.writerow([s["name"], s["requested_hosts"], s["allocated_cidr"], s["netmask"], s["usable_range"]])
            messagebox.showinfo("Başarılı", "CSV tablosu kaydedildi.")

if __name__ == "__main__":
    app = SubnetMasterApp()
    app.mainloop()