class ConfigGenerator:
    @staticmethod
    def generate_cisco(network_name: str, gateway_ip: str, netmask: str, interface: str = "GigabitEthernet0/1") -> str:
        return (
            f"! --- Cisco IOS Configuration [{network_name}] ---\n"
            f"interface {interface}\n"
            f" description Subnet_{network_name}\n"
            f" ip address {gateway_ip} {netmask}\n"
            f" no shutdown\n"
            f"exit\n"
        )

    @staticmethod
    def generate_mikrotik(network_name: str, gateway_ip: str, cidr_prefix: int, interface: str = "ether1") -> str:
        return (
            f"# --- MikroTik RouterOS Configuration [{network_name}] ---\n"
            f"/ip address\n"
            f"add address={gateway_ip}/{cidr_prefix} interface={interface} comment=\"Subnet_{network_name}\"\n"
        )