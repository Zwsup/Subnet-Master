import ipaddress

class NetworkValidator:
    @staticmethod
    def analyze_overlaps(cidr_list: list[str]) -> dict:
        """
        Verilen CIDR listesindeki ağların birbiriyle çakışıp çakışmadığını analiz eder.
        Örnek girdi: ['10.0.1.0/24', '10.0.1.128/25', '192.168.1.0/24']
        """
        valid_networks = []
        errors = []

        # 1. Sözdizimini kontrol et
        for cidr in cidr_list:
            cidr_clean = cidr.strip()
            if not cidr_clean:
                continue
            try:
                net = ipaddress.ip_network(cidr_clean, strict=False)
                valid_networks.append(net)
            except ValueError as e:
                errors.append(f"Geçersiz format: '{cidr_clean}' ({str(e)})")

        overlaps = []
        clean_networks = []

        # 2. İkili (Pairwise) Çakışma Kontrolü
        for i in range(len(valid_networks)):
            is_overlapping = False
            for j in range(i + 1, len(valid_networks)):
                net_a = valid_networks[i]
                net_b = valid_networks[j]

                if net_a.overlaps(net_b):
                    is_overlapping = True
                    overlaps.append({
                        "network_a": str(net_a),
                        "network_b": str(net_b),
                        "reason": f"'{net_a}' aralığı ile '{net_b}' aralığı birbiriyle kesişiyor!",
                        "range_a": f"{net_a[0]} - {net_a[-1]}",
                        "range_b": f"{net_b[0]} - {net_b[-1]}"
                    })
            if not is_overlapping:
                clean_networks.append(str(valid_networks[i]))

        return {
            "total_checked": len(valid_networks),
            "overlaps_found": len(overlaps),
            "overlaps": overlaps,
            "clean_networks": clean_networks,
            "errors": errors,
            "status": "DANGER" if overlaps or errors else "SAFE"
        }

    @staticmethod
    def audit_subnet_efficiency(cidr: str, active_hosts: int) -> dict:
        """
        Bir alt ağdaki IP israfını (Wastage) ve verimliliği denetler.
        """
        try:
            net = ipaddress.ip_network(cidr, strict=False)
            total_usable = max(0, net.num_addresses - 2)
            
            if active_hosts > total_usable:
                return {
                    "efficiency": 0,
                    "status": "OVERFLOW",
                    "message": f"Hata: {active_hosts} cihaz, bu ağın kapasitesinden ({total_usable}) büyük!"
                }

            efficiency = (active_hosts / total_usable) * 100 if total_usable > 0 else 0
            wasted_ips = total_usable - active_hosts

            recommendation = "Optimal kullanım."
            if efficiency < 15 and total_usable > 14:
                recommendation = f"Aşırı IP israfı (%{100-efficiency:.1f} boş). Daha küçük bir maske (örn: /28 veya /29) önerilir."

            return {
                "efficiency": round(efficiency, 1),
                "wasted_ips": wasted_ips,
                "recommendation": recommendation,
                "status": "GOOD" if efficiency >= 50 else "WARNING"
            }
        except Exception as e:
            return {"status": "ERROR", "message": str(e)}