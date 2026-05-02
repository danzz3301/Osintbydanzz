# ==================== PORT SCANNER MODULE ====================
# Lightweight Port Scanner menggunakan Socket Python
# Support untuk scan port pada device di jaringan lokal

import socket
import subprocess
import threading
from typing import Dict, List
from datetime import datetime
import sys

class PortScanner:
    def __init__(self, target_ip, start_port=1, end_port=1024):
        self.target_ip = target_ip
        self.start_port = start_port
        self.end_port = end_port
        self.open_ports = []
        self.closed_ports = []
        self.lock = threading.Lock()
        
        # Common port mapping
        self.common_ports = {
            21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP",
            53: "DNS", 80: "HTTP", 110: "POP3", 143: "IMAP",
            443: "HTTPS", 445: "SMB", 465: "SMTPS", 587: "SMTP",
            3306: "MySQL", 3389: "RDP", 5432: "PostgreSQL",
            5900: "VNC", 6379: "Redis", 8080: "HTTP Alt",
            8443: "HTTPS Alt", 9000: "SonarQube", 27017: "MongoDB",
            50070: "Hadoop NameNode", 4444: "Metasploit"
        }

    def validate_ip(self):
        pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        import re
        if not re.match(pattern, self.target_ip):
            return False
        parts = self.target_ip.split('.')
        for part in parts:
            try:
                if int(part) < 0 or int(part) > 255:
                    return False
            except:
                return False
        return True

    def scan_port(self, port):
        """Scan single port menggunakan socket"""
        try:
            # Create socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            
            # Attempt connection
            result = sock.connect_ex((self.target_ip, port))
            sock.close()
            
            with self.lock:
                if result == 0:
                    service = self.common_ports.get(port, "Unknown")
                    self.open_ports.append({"port": port, "service": service, "status": "OPEN"})
                else:
                    self.closed_ports.append(port)
        except Exception:
            pass

    def scan_network(self, threads=50):
        """Scan port range dengan multi-threading"""
        if not self.validate_ip():
            return {"error": "IP tidak valid"}
        
        thread_list = []
        
        # Multi-threaded port scanning
        for port in range(self.start_port, self.end_port + 1):
            thread = threading.Thread(target=self.scan_port, args=(port,))
            thread_list.append(thread)
            thread.start()
            
            # Limit concurrent threads
            if len(thread_list) >= threads:
                for t in thread_list:
                    t.join()
                thread_list = []
        
        # Wait for remaining threads
        for t in thread_list:
            t.join()
        
        return self.generate_report()

    def detect_service_version(self, port):
        """Coba deteksi versi service dengan banner grabbing"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            sock.connect((self.target_ip, port))
            
            # Send HTTP request untuk web services
            if port in [80, 8080, 8443, 443]:
                sock.send(b"GET / HTTP/1.0\r\n\r\n")
            
            # Receive banner
            banner = sock.recv(1024).decode('utf-8', errors='ignore')
            sock.close()
            
            # Extract version info
            if 'Server:' in banner:
                import re
                match = re.search(r'Server: ([^\r\n]+)', banner)
                if match:
                    return match.group(1)
            
            return None
        except:
            return None

    def detect_vulnerabilities(self):
        """Deteksi vulnerable services berdasarkan port yang terbuka"""
        vulnerabilities = []
        
        for port_info in self.open_ports:
            port = port_info['port']
            service = port_info['service']
            
            # Known vulnerabilities mapping
            vuln_map = {
                21: {"name": "FTP", "risk": "🔴 HIGH", "issues": ["Plaintext credentials", "No encryption"]},
                23: {"name": "Telnet", "risk": "🔴 HIGH", "issues": ["Plaintext login", "No encryption", "Deprecated"]},
                445: {"name": "SMB", "risk": "🔴 HIGH", "issues": ["EternalBlue (CVE-2017-0144)", "Ransomware vector"]},
                3389: {"name": "RDP", "risk": "🟠 MEDIUM", "issues": ["Brute force attacks", "Credential theft"]},
                3306: {"name": "MySQL", "risk": "🟠 MEDIUM", "issues": ["Unprotected database", "SQL injection"]},
                5432: {"name": "PostgreSQL", "risk": "🟠 MEDIUM", "issues": ["Unprotected database", "Default credentials"]},
                5900: {"name": "VNC", "risk": "🟠 MEDIUM", "issues": ["Weak encryption", "Credential exposure"]},
                27017: {"name": "MongoDB", "risk": "🔴 HIGH", "issues": ["No authentication", "Data exposure"]},
                6379: {"name": "Redis", "risk": "🔴 HIGH", "issues": ["No authentication", "RCE possible"]},
                50070: {"name": "Hadoop", "risk": "🔴 HIGH", "issues": ["Unprotected namenode", "Data access"]},
            }
            
            if port in vuln_map:
                vulnerabilities.append({
                    "port": port,
                    "service": service,
                    "vulnerability": vuln_map[port]
                })
        
        return vulnerabilities

    def generate_report(self):
        """Generate detailed port scan report"""
        report = {
            "target": self.target_ip,
            "scan_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "port_range": f"{self.start_port}-{self.end_port}",
            "total_scanned": self.end_port - self.start_port + 1,
            "open_ports": self.open_ports,
            "closed_ports": len(self.closed_ports),
            "vulnerabilities": self.detect_vulnerabilities()
        }
        return report

    def generate_report_text(self):
        """Generate text format report untuk Telegram"""
        report = self.generate_report()
        
        lines = []
        lines.append("🔍 PORT SCAN REPORT - LENGKAP")
        lines.append("═══════════════════════════════════")
        lines.append(f"\n🎯 Target: {report['target']}")
        lines.append(f"📊 Range: Port {report['port_range']}")
        lines.append(f"🕐 Waktu: {report['scan_time']}")
        lines.append(f"\n📈 STATISTIK:")
        lines.append(f"   • Total Port Scanned: {report['total_scanned']}")
        lines.append(f"   • Port Terbuka: {len(report['open_ports'])} ✅")
        lines.append(f"   • Port Tertutup: {report['closed_ports']} ❌")
        
        if report['open_ports']:
            lines.append(f"\n🔓 PORT TERBUKA:")
            lines.append("───────────────────────────────────")
            for port_info in sorted(report['open_ports'], key=lambda x: x['port']):
                lines.append(f"   • {port_info['port']}/TCP - {port_info['service']} ✅")
        
        if report['vulnerabilities']:
            lines.append(f"\n⚠️ VULNERABILITIES TERDETEKSI ({len(report['vulnerabilities'])} issues):")
            lines.append("───────────────────────────────────")
            for vuln in report['vulnerabilities']:
                lines.append(f"\n   {vuln['vulnerability']['risk']} Port {vuln['port']}/{vuln['service']}")
                lines.append(f"      Issues:")
                for issue in vuln['vulnerability']['issues']:
                    lines.append(f"      • {issue}")
        else:
            lines.append(f"\n✅ Tidak ada vulnerability terdeteksi di port yang terbuka")
        
        lines.append("\n═══════════════════════════════════")
        lines.append("⚠️ HANYA UNTUK TESTING AUTHORIZED!")
        lines.append("🔒 Scanning tanpa izin adalah ILLEGAL")
        
        return "\n".join(lines)
