import ipaddress

class NetworkSummarizer:
    @staticmethod
    def summarize_networks(cidr_list: list[str]) -> dict:
        """
        Verilen alt ağ listesini kapsayan en küçük özet ağı (Supernet) bulur.
        Örn: ['192.168.0.0/24', '192.168.1.0/24', '192.168.2.0/24', '192.168.3.0/24']
        Sonuç -> '192.168.0.0/22'
        """
        valid_nets = []
        errors = []

        for cidr in cidr_list:
            clean = cidr.strip()
            if not clean:
                continue
            try:
                valid_nets.append(ipaddress.ip_network(clean, strict=False))
            except ValueError as e:
                errors.append(f"Geçersiz format: '{clean}' ({str(e)})")

        if not valid_nets:
            return {"status": "ERROR", "message": "Geçerli hiçbir alt ağ bulunamadı.", "errors": errors}

        # Python ipaddress kütüphanesi collapse_addresses ile bitişik ve kapsanan ağları sadeleştirir
        # Ancak tam bir "Summary Route" (tek bir süper blok) bulmak için minimum kapsayıcıyı biz hesaplarız:
        min_ip = min(net.network_address for net in valid_nets)
        max_ip = max(net.broadcast_address for net in valid_nets)

        # 32 bitlik ikili gösteriminde ortak prefix uzunluğunu bulalım
        bin_min = f"{int(min_ip):032b}"
        bin_max = f"{int(max_ip):032b}"

        common_prefix_len = 0
        for i in range(32):
            if bin_min[i] == bin_max[i]:
                common_prefix_len += 1
            else:
                break

        summary_network = ipaddress.ip_network(f"{min_ip}/{common_prefix_len}", strict=False)

        # İsraf (Wastage) Analizi: Özet ağın toplam kapasitesi ile girilen ağların toplam kapasitesi arasındaki fark
        total_summary_ips = summary_network.num_addresses
        total_input_ips = sum(net.num_addresses for net in valid_nets)
        wasted_ips = total_summary_ips - total_input_ips
        efficiency = (total_input_ips / total_summary_ips) * 100 if total_summary_ips > 0 else 0

        # Router Komutları
        static_route_cisco = f"ip route {summary_network.network_address} {summary_network.netmask} Null0"
        bgp_cisco = f"aggregate-address {summary_network.network_address} {summary_network.netmask} summary-only"
        route_mikrotik = f"/ip route add dst-address={summary_network} type=blackhole comment=\"Summary_Route\""

        return {
            "status": "SUCCESS",
            "summary_cidr": str(summary_network),
            "summary_netmask": str(summary_network.netmask),
            "total_summary_ips": total_summary_ips,
            "total_input_ips": total_input_ips,
            "wasted_ips": wasted_ips,
            "efficiency": round(efficiency, 1),
            "network_count": len(valid_nets),
            "static_route_cisco": static_route_cisco,
            "bgp_cisco": bgp_cisco,
            "route_mikrotik": route_mikrotik,
            "errors": errors
        }