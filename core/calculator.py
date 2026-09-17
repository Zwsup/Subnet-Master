import ipaddress
import math
from core.converter import NetworkConverter

class SubnetCalculator:
    @staticmethod
    def calculate_subnet(ip_with_prefix: str) -> dict:
        try:
            net = ipaddress.ip_network(ip_with_prefix, strict=False)
            hosts = list(net.hosts())
            ip_info = NetworkConverter.get_ip_class_and_type(str(net.network_address))
            
            return {
                "network_address": str(net.network_address),
                "netmask": str(net.netmask),
                "wildcard_mask": str(net.hostmask),
                "broadcast_address": str(net.broadcast_address),
                "total_hosts": net.num_addresses,
                "usable_hosts": len(hosts),
                "first_host": str(hosts[0]) if hosts else "N/A",
                "last_host": str(hosts[-1]) if hosts else "N/A",
                "cidr": f"/{net.prefixlen}",
                "prefix_len": net.prefixlen,
                "ip_class": ip_info["class"],
                "ip_type": ip_info["is_private"],
                "net_binary": NetworkConverter.ip_to_binary(str(net.network_address)),
                "mask_binary": NetworkConverter.ip_to_binary(str(net.netmask))
            }
        except ValueError as e:
            raise ValueError(f"Geçersiz IP veya Prefiks: {e}")

    @staticmethod
    def calculate_vlsm(base_network: str, requirements: list[dict]) -> dict:
        net = ipaddress.ip_network(base_network, strict=False)
        sorted_reqs = sorted(requirements, key=lambda x: x['hosts'], reverse=True)
        
        current_ip = net.network_address
        results = []
        total_allocated_addresses = 0

        for req in sorted_reqs:
            needed_hosts = req['hosts']
            total_needed = needed_hosts + 2
            prefix = 32 - math.ceil(math.log2(total_needed))
            
            sub_net = ipaddress.ip_network(f"{current_ip}/{prefix}", strict=False)
            
            if sub_net.broadcast_address > net.broadcast_address:
                raise ValueError("Ana ağ kapasitesi belirtilen ihtiyaçlar için yetersiz!")

            hosts = list(sub_net.hosts())
            results.append({
                "name": req['name'],
                "requested_hosts": needed_hosts,
                "allocated_cidr": f"{sub_net.network_address}/{prefix}",
                "network_address": str(sub_net.network_address),
                "netmask": str(sub_net.netmask),
                "gateway_ip": str(hosts[0]) if hosts else "N/A",
                "usable_range": f"{hosts[0]} - {hosts[-1]}" if hosts else "N/A",
                "total_usable": len(hosts),
                "prefix": prefix
            })
            
            total_allocated_addresses += sub_net.num_addresses
            current_ip = sub_net.broadcast_address + 1

        usage_ratio = total_allocated_addresses / net.num_addresses

        return {
            "subnets": results,
            "total_allocated": total_allocated_addresses,
            "total_capacity": net.num_addresses,
            "usage_ratio": min(usage_ratio, 1.0)
        }