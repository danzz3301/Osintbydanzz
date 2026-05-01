# osintbyndanzz.py - OSINT Bot Telegram Ultimate
# Dibuat oleh danzz³³⁰1
# HANYA UNTUK PEMBELAJARAN DI LAB SENDIRI

import os
import re
import socket
import subprocess
import requests
import phonenumbers
from phonenumbers import carrier, geocoder, timezone
from datetime import datetime
from typing import List, Dict
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

# ==================== KONFIGURASI ====================
BOT_TOKEN = "8443250017:AAEW3U7r8Xkcj-C1aVIOgEM3ceUc-Q8w6Bo"
ALLOWED_CHAT_IDS = [7680161554]
CREATOR = "danzz³³⁰1"
BOT_NAME = "danzzosint"

WORK_DIR = os.path.expanduser("~/storage/downloads/osint_temp")
os.makedirs(WORK_DIR, exist_ok=True)

# ==================== IP OSINT DENGAN LINK MAPS ====================
class IPOSINT:
    def __init__(self, ip_address):
        self.ip = ip_address.strip()
        self.raw_data = None

    def validate_ip(self):
        pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if not re.match(pattern, self.ip):
            return False
        parts = self.ip.split('.')
        for part in parts:
            if int(part) < 0 or int(part) > 255:
                return False
        return True

    def get_geolocation(self):
        if not self.validate_ip():
            return {"error": "Format IP tidak valid"}
        try:
            url = f"http://ip-api.com/json/{self.ip}?fields=66846719"
            response = requests.get(url, timeout=10)
            data = response.json()
            if data.get('status') == 'success':
                self.raw_data = data
                return data
            return {"error": data.get('message', 'Unknown error')}
        except Exception as e:
            return {"error": str(e)}

    def get_maps_link(self, lat, lon):
        if lat and lon and lat != 'N/A' and lon != 'N/A':
            return f"https://www.google.com/maps?q={lat},{lon}"
        return None

    def generate_report_text(self):
        geo = self.get_geolocation()
        if "error" in geo:
            return f"❌ Error: {geo['error']}"

        lat = geo.get('lat', 'N/A')
        lon = geo.get('lon', 'N/A')
        maps_link = self.get_maps_link(lat, lon)

        report = f"""
🌐 IP GEOLOCATION REPORT - REAL TIME
═══════════════════════════════════

📡 IP Address: {self.ip}
🕐 Waktu: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📍 LOKASI REAL-TIME:
   • 🌍 Negara: {geo.get('country', 'N/A')} ({geo.get('countryCode', 'N/A')})
   • 🏙️ Region: {geo.get('regionName', 'N/A')}
   • 🏢 Kota: {geo.get('city', 'N/A')}
   • 📮 Kode Pos: {geo.get('zip', 'N/A')}
   • ⏰ Zona Waktu: {geo.get('timezone', 'N/A')}

🗺️ KOORDINAT & MAPS:
   • 📐 Latitude: {lat}
   • 📐 Longitude: {lon}
   • 🗺️ Google Maps: {maps_link if maps_link else 'Tidak tersedia'}

🔧 NETWORK DETAIL:
   • 📡 ISP: {geo.get('isp', 'N/A')}
   • 🏢 Organisasi: {geo.get('org', 'N/A')}
   • 🔗 AS Number: {geo.get('as', 'N/A')}

🛡️ KEAMANAN:
   • 🔒 Proxy/VPN: {'✅ YA - Terdeteksi' if geo.get('proxy', False) else '❌ TIDAK'}
   • 📱 Mobile: {'✅ YA' if geo.get('mobile', False) else '❌ TIDAK'}
   • ☁️ Hosting: {'✅ YA' if geo.get('hosting', False) else '❌ TIDAK'}

═══════════════════════════════════
⚠️ HANYA UNTUK PEMBELAJARAN!
📱 Dibuat oleh: {CREATOR}
═══════════════════════════════════
"""
        return report

# ==================== PHONE OSINT ====================
class PhoneOSINT:
    def __init__(self, phone_number):
        self.raw_number = phone_number
        self.parsed_number = None
        self.is_valid = False
        self.country_code = None
        self.national_number = None

    def parse_number(self):
        try:
            self.parsed_number = phonenumbers.parse(self.raw_number, None)
            self.is_valid = phonenumbers.is_valid_number(self.parsed_number)
            if self.is_valid:
                self.country_code = self.parsed_number.country_code
                self.national_number = str(self.parsed_number.national_number)
            return self.is_valid
        except Exception:
            return False

    def get_carrier_info(self):
        if not self.is_valid:
            return "Nomor tidak valid"
        try:
            carrier_name = carrier.name_for_number(self.parsed_number, "id")
            return carrier_name if carrier_name else "Tidak diketahui"
        except:
            return "Tidak dapat menentukan carrier"

    def get_location_info(self):
        if not self.is_valid:
            return "Nomor tidak valid"
        try:
            location = geocoder.description_for_number(self.parsed_number, "id")
            return location if location else "Tidak diketahui"
        except:
            return "Tidak dapat menentukan lokasi"

    def get_timezone_info(self):
        if not self.is_valid:
            return "Nomor tidak valid"
        try:
            tzones = timezone.time_zones_for_number(self.parsed_number)
            return ", ".join(tzones) if tzones else "Tidak diketahui"
        except:
            return "Tidak dapat menentukan timezone"

    def get_number_type(self):
        if not self.is_valid:
            return "Nomor tidak valid"
        num_type = phonenumbers.number_type(self.parsed_number)
        types = {0: "FIXED_LINE", 1: "MOBILE", 2: "FIXED_LINE_OR_MOBILE", 3: "TOLL_FREE", 
                 4: "PREMIUM_RATE", 5: "SHARED_COST", 6: "VOIP", 7: "PERSONAL_NUMBER", 
                 8: "PAGER", 9: "UAN", 10: "VOICEMAIL", 11: "UNKNOWN"}
        return types.get(num_type, "UNKNOWN")

    def generate_report_text(self):
        if not self.parse_number():
            return "❌ Error: Nomor telepon tidak valid!\n\nGunakan format: +628123456789"

        report = f"""
📞 PHONE OSINT REPORT - LENGKAP
═══════════════════════════════════

📱 Nomor: {self.raw_number}
✅ Validasi: {'✅ VALID' if self.is_valid else '❌ INVALID'}

🌍 FORMAT STANDAR:
   • International: {phonenumbers.format_number(self.parsed_number, phonenumbers.PhoneNumberFormat.INTERNATIONAL)}
   • Nasional: {phonenumbers.format_number(self.parsed_number, phonenumbers.PhoneNumberFormat.NATIONAL)}
   • E164: {phonenumbers.format_number(self.parsed_number, phonenumbers.PhoneNumberFormat.E164)}

📊 INFORMASI DETAIL:
   • 🌍 Kode Negara: +{self.country_code}
   • 🔢 Nomor Nasional: {self.national_number}
   • 📡 Provider: {self.get_carrier_info()}
   • 📍 Lokasi: {self.get_location_info()}
   • ⏰ Zona Waktu: {self.get_timezone_info()}
   • 🏷️ Tipe: {self.get_number_type()}

🔍 LINK PENCARIAN:
   • WhatsApp: https://wa.me/{self.raw_number.replace('+', '')}
   • Google Search: https://www.google.com/search?q={self.raw_number}
   • Truecaller: https://www.truecaller.com/search

═══════════════════════════════════
⚠️ HANYA UNTUK PEMBELAJARAN!
📱 Dibuat oleh: {CREATOR}
═══════════════════════════════════
"""
        return report

# ==================== PHOTO OSINT ====================
class PhotoOSINT:
    def __init__(self, photo_path):
        self.photo_path = photo_path
        self.exif_data = {}
        self.gps_coords = None

    def extract_all_exif(self):
        try:
            image = Image.open(self.photo_path)
            exif = image._getexif()
            if not exif:
                return {"error": "Tidak ada metadata EXIF"}
            for tag_id, value in exif.items():
                tag_name = TAGS.get(tag_id, tag_id)
                if isinstance(value, bytes):
                    value = value.decode('utf-8', errors='ignore')
                self.exif_data[tag_name] = value
            return self.exif_data
        except Exception as e:
            return {"error": str(e)}

    def extract_gps(self):
        try:
            image = Image.open(self.photo_path)
            exif = image._getexif()
            if not exif:
                return None
            gps_info = {}
            for tag_id, value in exif.items():
                tag_name = TAGS.get(tag_id, tag_id)
                if tag_name == 'GPSInfo':
                    for gps_tag_id, gps_value in value.items():
                        gps_tag_name = GPSTAGS.get(gps_tag_id, gps_tag_id)
                        gps_info[gps_tag_name] = gps_value
            if 'GPSLatitude' in gps_info and 'GPSLongitude' in gps_info:
                lat = gps_info['GPSLatitude']
                lon = gps_info['GPSLongitude']
                lat_ref = gps_info.get('GPSLatitudeRef', 'N')
                lon_ref = gps_info.get('GPSLongitudeRef', 'E')
                latitude = lat[0] + lat[1]/60 + lat[2]/3600
                longitude = lon[0] + lon[1]/60 + lon[2]/3600
                if lat_ref == 'S': latitude = -latitude
                if lon_ref == 'W': longitude = -longitude
                self.gps_coords = (latitude, longitude)
                return self.gps_coords
            return None
        except Exception:
            return None

    def get_maps_link(self):
        if self.gps_coords:
            return f"https://www.google.com/maps?q={self.gps_coords[0]},{self.gps_coords[1]}"
        return None

    def generate_report_text(self):
        lines = []
        lines.append("📸 PHOTO OSINT REPORT - LENGKAP")
        lines.append("═══════════════════════════════════")

        file_info = {
            "file_name": os.path.basename(self.photo_path),
            "file_size": os.path.getsize(self.photo_path),
        }
        lines.append(f"\n📁 INFORMASI FILE:")
        lines.append(f"   • Nama: {file_info['file_name']}")
        lines.append(f"   • Ukuran: {file_info['file_size']} bytes")

        lines.append("\n📷 METADATA EXIF:")
        exif = self.extract_all_exif()
        if "error" in exif:
            lines.append(f"   • {exif['error']}")
        else:
            important_tags = ['DateTime', 'Make', 'Model', 'Software', 'FNumber', 'ExposureTime', 'ISOSpeedRatings']
            for tag in important_tags:
                if tag in exif:
                    lines.append(f"   • {tag}: {exif[tag]}")

        lines.append("\n📍 INFORMASI LOKASI GPS:")
        gps = self.extract_gps()
        if gps:
            maps_link = self.get_maps_link()
            lines.append(f"   • Latitude: {gps[0]:.6f}")
            lines.append(f"   • Longitude: {gps[1]:.6f}")
            lines.append(f"   • 🗺️ Google Maps: {maps_link}")
        else:
            lines.append("   • ❌ Tidak ada data GPS dalam foto ini")
            lines.append("   • Penyebab: GPS mati, foto diedit, atau lewat WA")

        lines.append("\n═══════════════════════════════════")
        lines.append(f"⚠️ HANYA UNTUK FOTO ANDA SENDIRI!")
        lines.append(f"📱 Dibuat oleh: {CREATOR}")
        return "\n".join(lines)

# ==================== NETWORK SCANNER (DIPERBAIKI DENGAN DETEKSI NAMA) ====================
class NetworkScanner:
    def __init__(self):
        self.devices = []

    def get_my_ip_method1(self):
        """Method 1: hostname -I (Termux)"""
        try:
            result = subprocess.run(['hostname', '-I'], capture_output=True, text=True, timeout=5)
            if result.stdout.strip():
                ips = result.stdout.strip().split()
                for ip in ips:
                    if ip.startswith(('192.168.', '10.', '172.16.', '172.17.', '172.18.', '172.19.', '172.20.', '172.21.', '172.22.', '172.23.', '172.24.', '172.25.', '172.26.', '172.27.', '172.28.', '172.29.', '172.30.', '172.31.')):
                        return ip
                return ips[0] if ips else None
        except:
            pass
        return None

    def get_my_ip_method2(self):
        """Method 2: ip route (Linux)"""
        try:
            result = subprocess.run(['ip', 'route'], capture_output=True, text=True, timeout=5)
            for line in result.stdout.split('\n'):
                if 'src' in line:
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == 'src' and i + 1 < len(parts):
                            ip = parts[i + 1]
                            if ip.startswith(('192.168.', '10.', '172.')):
                                return ip
        except:
            pass
        return None

    def get_my_ip_method3(self):
        """Method 3: ifconfig (alternative)"""
        try:
            result = subprocess.run(['ifconfig'], capture_output=True, text=True, timeout=5)
            lines = result.stdout.split('\n')
            for line in lines:
                match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)', line)
                if match:
                    ip = match.group(1)
                    if ip.startswith(('192.168.', '10.', '172.')) and ip != '127.0.0.1':
                        return ip
        except:
            pass
        return None

    def get_my_ip_method4(self):
        """Method 4: API eksternal (last resort)"""
        try:
            response = requests.get('https://api.ipify.org', timeout=5)
            if response.status_code == 200:
                return response.text.strip()
        except:
            pass
        return None

    def get_my_ip(self):
        ip = self.get_my_ip_method1()
        if ip: return ip
        ip = self.get_my_ip_method2()
        if ip: return ip
        ip = self.get_my_ip_method3()
        if ip: return ip
        ip = self.get_my_ip_method4()
        return ip

    def get_hostname_reverse_dns(self, ip):
        """Method 1: Reverse DNS lookup"""
        try:
            hostname = socket.gethostbyaddr(ip)[0]
            if hostname and hostname != ip:
                # Bersihkan hostname
                hostname = hostname.split('.')[0]
                if hostname and 'unknown' not in hostname.lower():
                    return hostname
        except:
            pass
        return None

    def get_hostname_nmap(self, ip):
        """Method 2: Nmap scan (paling akurat)"""
        try:
            result = subprocess.run(['nmap', '-sn', ip], capture_output=True, text=True, timeout=10)
            for line in result.stdout.split('\n'):
                if 'Nmap scan report for' in line:
                    parts = line.replace('Nmap scan report for', '').strip()
                    if '(' in parts and ')' in parts:
                        hostname = parts.split('(')[0].strip()
                        if hostname and hostname != '' and 'unknown' not in hostname.lower():
                            return hostname
                    elif parts and '.' in parts:
                        hostname = parts.split('.')[0]
                        if hostname and 'unknown' not in hostname.lower():
                            return hostname
        except:
            pass
        return None

    def get_hostname_arp(self, ip):
        """Method 3: ARP table + vendor detection"""
        try:
            result = subprocess.run(['arp', '-a', ip], capture_output=True, text=True, timeout=5)
            line = result.stdout.strip()
            # Cari MAC address
            mac_match = re.search(r'([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})', line)
            if mac_match:
                mac = mac_match.group(0).upper()
                # Deteksi vendor dari MAC prefix (OUI)
                mac_prefix = mac[:8].replace(':', '').replace('-', '').upper()
                vendors = {
                    'DCA632': 'Xiaomi', 'C83A35': 'Xiaomi', '8C4B14': 'Xiaomi',
                    'F0D1A9': 'Samsung', '7830E1': 'Samsung', 'D0667D': 'Samsung',
                    'AC8257': 'Apple', 'C0A0BB': 'Apple', '8CB1D1': 'Apple',
                    'B0A7B9': 'OPPO', 'C0A0BB': 'Vivo', '68DBF5': 'Realme',
                    'D4D1E9': 'Lenovo', 'E03B4E': 'Huawei', 'D4543A': 'TP-Link',
                    '00259C': 'Intel', 'F8B156': 'Intel', 'B888E3': 'Realtek'
                }
                for prefix, vendor in vendors.items():
                    if mac_prefix.startswith(prefix):
                        return vendor
            return None
        except:
            pass
        return None

    def get_hostname_mdns(self, ip):
        """Method 4: mDNS/Avahi (perangkat Apple, Linux, printer)"""
        try:
            result = subprocess.run(['avahi-resolve', '-a', ip], capture_output=True, text=True, timeout=5)
            if result.stdout.strip():
                parts = result.stdout.strip().split()
                if len(parts) >= 2:
                    hostname = parts[1].split('.')[0]
                    if hostname and 'unknown' not in hostname.lower():
                        return hostname
        except:
            pass
        return None

    def get_hostname_ping(self, ip):
        """Method 5: Ping dengan NetBIOS"""
        try:
            result = subprocess.run(['ping', '-c', '1', ip], capture_output=True, text=True, timeout=5)
            # Ping terkadang bisa dapat hostname di output
            for line in result.stdout.split('\n'):
                if 'from' in line.lower() and '(' in line:
                    match = re.search(r'from\s+([a-zA-Z0-9\-\.]+)', line.lower())
                    if match:
                        hostname = match.group(1).split('.')[0]
                        if hostname and hostname != ip and 'unknown' not in hostname.lower():
                            return hostname
        except:
            pass
        return None

    def is_gateway(self, ip, gateway_ip):
        """Cek apakah IP adalah gateway/router"""
        if ip == gateway_ip or ip.endswith('.1') or ip.endswith('.254'):
            return True
        return False

    def get_device_name(self, ip, gateway_ip=None):
        """Coba semua metode untuk dapat nama perangkat"""
        # Jika ini gateway
        if self.is_gateway(ip, gateway_ip):
            return "Router/Gateway"
        
        # Jika ini IP sendiri
        my_ip = self.get_my_ip()
        if ip == my_ip:
            return "Device Anda"
        
        # Coba semua metode
        name = self.get_hostname_reverse_dns(ip)
        if name: return name
        
        name = self.get_hostname_nmap(ip)
        if name: return name
        
        name = self.get_hostname_arp(ip)
        if name: return name
        
        name = self.get_hostname_mdns(ip)
        if name: return name
        
        name = self.get_hostname_ping(ip)
        if name: return name
        
        return "Unknown"

    def scan_network(self):
        devices = []
        my_ip = self.get_my_ip()
        
        if not my_ip:
            return [{'error': 'Tidak dapat mendeteksi IP sendiri. Pastikan terhubung ke WiFi.'}]
        
        # Deteksi network prefix
        if '.' in my_ip:
            ip_parts = my_ip.split('.')
            if len(ip_parts) >= 3:
                network_prefix = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}"
            else:
                network_prefix = "192.168.1"
        else:
            network_prefix = "192.168.1"
        
        # Deteksi gateway (biasanya .1 atau .254)
        gateway_ip = f"{network_prefix}.1"
        
        # Scan dengan ping
        for i in range(1, 255):
            ip = f"{network_prefix}.{i}"
            try:
                result = subprocess.run(['ping', '-c', '1', '-W', '1', ip],
                                        capture_output=True, text=True, timeout=2)
                if result.returncode == 0:
                    # Dapatkan nama perangkat
                    name = self.get_device_name(ip, gateway_ip)
                    devices.append({'ip': ip, 'hostname': name})
            except:
                continue
        
        return devices

    def generate_report(self):
        my_ip = self.get_my_ip()
        
        if not my_ip:
            return """
❌ ERROR: Tidak dapat mendeteksi koneksi jaringan!

SOLUSI:
1. Pastikan TERHUBUNG ke WiFi/Hotspot
2. Buka Termux, ketik: termux-setup-storage
3. Beri izin akses lokasi (jika diminta)
4. Restart Termux
5. Jalankan ulang bot

ATAU coba perinttah manual:
• ping 8.8.8.8 (test koneksi)
• apt update && apt upgrade
• pkg install nmap

═══════════════════════════════════
⚠️ Dibuat oleh: danzz³³⁰1
"""
        devices = self.scan_network()

        lines = []
        lines.append("🌐 NETWORK SCAN REPORT - LENGKAP")
        lines.append("═══════════════════════════════════")
        lines.append(f"\n📡 IP Anda: {my_ip}")
        
        # Deteksi network
        if '.' in my_ip:
            ip_parts = my_ip.split('.')
            if len(ip_parts) >= 3:
                lines.append(f"📡 Jaringan: {ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.0/24")
        
        lines.append(f"📊 Total Perangkat: {len(devices)}")
        
        if not devices or len(devices) <= 1:
            lines.append("\n⚠️ Tidak ada perangkat lain yang terdeteksi!")
            lines.append("\nKemungkinan penyebab:")
            lines.append("• Firewall perangkat lain memblokir ping")
            lines.append("• Perangkat dalam mode sleep/power saving")
            lines.append("• Coba scan dengan nmap: pkg install nmap")
        else:
            lines.append("\n📱 DAFTAR PERANGKAT TERHUBUNG:")
            lines.append("───────────────────────────────────")
            for i, device in enumerate(devices[:25], 1):
                lines.append(f"\n{i}. IP: {device.get('ip', 'N/A')}")
                nama = device.get('hostname', 'Unknown')
                if nama == "Unknown":
                    lines.append(f"   📛 Nama: {nama} (tidak terdeteksi)")
                else:
                    lines.append(f"   📛 Nama: {nama}")
        
        lines.append("\n═══════════════════════════════════")
        lines.append("💡 INFO:")
        lines.append("   • 'Unknown' = perangkat tidak membagikan nama")
        lines.append("   • Install nmap untuk deteksi lebih akurat:")
        lines.append("     pkg install nmap")
        lines.append("\n═══════════════════════════════════")
        lines.append(f"⚠️ HANYA UNTUK JARINGAN ANDA SENDIRI!")
        lines.append(f"📱 Dibuat oleh: {CREATOR}")
        return "\n".join(lines)

# ==================== FUNGSI BANTUAN ====================
def get_temp_path(chat_id, prefix="photo"):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    return os.path.join(WORK_DIR, f"{prefix}_{chat_id}_{timestamp}.jpg")

def is_valid_ip(ip):
    pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
    if not re.match(pattern, ip):
        return False
    parts = ip.split('.')
    for part in parts:
        if int(part) < 0 or int(part) > 255:
            return False
    return True

def is_valid_phone(text):
    pattern = r'^\+\d{8,15}$'
    return re.match(pattern, text.strip()) is not None

# ==================== HANDLER TELEGRAM ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in ALLOWED_CHAT_IDS:
        await update.message.reply_text("❌ Akses Ditolak")
        return

    keyboard = [
        [InlineKeyboardButton("📸 PHOTO OSINT", callback_data="menu_photo"),
         InlineKeyboardButton("📞 PHONE OSINT", callback_data="menu_phone")],
        [InlineKeyboardButton("🌐 IP TRACKER", callback_data="menu_ip"),
         InlineKeyboardButton("📡 NETWORK SCAN", callback_data="menu_net")],
        [InlineKeyboardButton("🗺️ GOOGLE MAPS", callback_data="menu_maps"),
         InlineKeyboardButton("❓ BANTUAN", callback_data="menu_help")],
        [InlineKeyboardButton("ℹ️ INFO BOT", callback_data="menu_info")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = f"""
🤖 {BOT_NAME.upper()} - OSINT PRO ULTIMATE 🔍
═══════════════════════════════════
👤 Dibuat oleh: {CREATOR}

📌 FITUR LENGKAP OSINT:
   📸 • Photo OSINT (EXIF/GPS/Metadata)
   📞 • Phone OSINT (Provider/Lokasi/Timezone)
   🌐 • IP Tracker (Real-time + Maps)
   📡 • Network Scanner (WiFi/LAN + Deteksi Nama)
   🗺️ • Google Maps Integration

📱 CARA PENGGUNAAN:
   • Kirim FOTO → Analisis metadata & GPS
   • Kirim NOMOR (+62xxx) → Cek provider & lokasi
   • Kirim IP (8.8.8.8) → Lacak lokasi real-time
   • /scan → Scan jaringan sendiri

═══════════════════════════════════
⚠️ HANYA UNTUK PEMBELAJARAN!
🛡️ Jangan gunakan untuk melacak orang lain
"""
    await update.message.reply_text(text, reply_markup=reply_markup)

async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "menu_photo":
        text = """
📸 PHOTO OSINT
═══════════════════════════════════

Cara Penggunaan:
Kirimkan FOTO ke bot ini.

Informasi yang ditampilkan:
   • Metadata EXIF (kamera, tanggal, software)
   • Koordinat GPS (jika ada)
   • Link Google Maps langsung
   • Ukuran dan nama file

⚠️ HANYA UNTUK FOTO ANDA SENDIRI!
"""
        await query.edit_message_text(text)
    elif query.data == "menu_phone":
        text = """
📞 PHONE OSINT
═══════════════════════════════════

Cara Penggunaan:
Kirimkan NOMOR TELEPON dengan format:
+628123456789

Informasi yang ditampilkan:
   • Validasi nomor
   • Provider/Carrier
   • Lokasi geografis
   • Zona waktu
   • Tipe nomor
   • Link WhatsApp & Truecaller

⚠️ HANYA UNTUK PEMBELAJARAN!
"""
        await query.edit_message_text(text)
    elif query.data == "menu_ip":
        text = """
🌐 IP GEOLOCATION TRACKER
═══════════════════════════════════

Cara Penggunaan:
Kirimkan IP ADDRESS atau gunakan perintah:
/ip 8.8.8.8

Informasi yang ditampilkan:
   • Negara, region, kota
   • Koordinat (latitude/longitude)
   • ISP & Organisasi
   • Deteksi Proxy/VPN
   • Link Google Maps

⚠️ LOKASI BERDASARKAN PERKIRAAN ISP!
"""
        await query.edit_message_text(text)
    elif query.data == "menu_net":
        text = """
📡 NETWORK SCANNER
═══════════════════════════════════

Cara Penggunaan:
Gunakan perintah /scan untuk memulai scan.

Informasi yang ditampilkan:
   • IP Anda sendiri
   • Semua IP yang terhubung ke jaringan
   • Nama perangkat (jika terdeteksi)
   • Total perangkat terdeteksi

⚠️ HANYA UNTUK JARINGAN ANDA SENDIRI!
"""
        await query.edit_message_text(text)
    elif query.data == "menu_maps":
        text = """
🗺️ GOOGLE MAPS INTEGRATION
═══════════════════════════════════

Fitur Maps:
Setiap hasil analisis yang memiliki koordinat
(GPS dari foto atau IP address) akan disertakan
link Google Maps langsung!

Cara menggunakan link:
1. Klik link yang muncul di hasil
2. Akan terbuka Google Maps
3. Lihat lokasi di peta

⚠️ Lokasi berdasarkan perkiraan (tidak 100% akurat)
"""
        await query.edit_message_text(text)
    elif query.data == "menu_help":
        text = f"""
❓ BANTUAN {BOT_NAME.upper()}
═══════════════════════════════════

📌 DAFTAR PERINTAH:

/start - Menu utama
/help - Bantuan ini
/scan - Scan jaringan lokal
/ip <alamat> - Lacak IP address

📌 AUTO-DETECT (Kirim Langsung):

• 📸 FOTO → Analisis metadata & GPS
• 📞 NOMOR (+62xxx) → Analisis provider
• 🌐 IP (1.1.1.1) → Geolokasi

═══════════════════════════════════
Dibuat oleh: {CREATOR}
"""
        await query.edit_message_text(text)
    elif query.data == "menu_info":
        text = f"""
ℹ️ INFO BOT {BOT_NAME.upper()}
═══════════════════════════════════

🤖 Nama: {BOT_NAME.upper()}
👨‍💻 Creator: {CREATOR}
📦 Versi: 3.0 - Ultimate
🖥️ Platform: Termux / Linux

📚 LIBRARY YANG DIGUNAKAN:
   • python-telegram-bot v20+
   • Pillow (EXIF metadata)
   • phonenumbers (Phone OSINT)
   • requests (IP API)

🔧 FITUR LENGKAP:
   ✓ Photo OSINT (EXIF/GPS)
   ✓ Phone OSINT (Carrier/Lokasi)
   ✓ IP Geolocation Tracker
   ✓ Network Scanner (dengan deteksi nama)
   ✓ Google Maps Integration

═══════════════════════════════════
⚠️ HANYA UNTUK LAB SENDIRI!
"""
        await query.edit_message_text(text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in ALLOWED_CHAT_IDS:
        return

    text = f"""
❓ BANTUAN {BOT_NAME.upper()} PRO
═══════════════════════════════════

📌 DAFTAR PERINTAH:

/start - Menu utama interaktif
/help - Bantuan lengkap
/scan - Scan jaringan sendiri
/ip <alamat> - Lacak IP real-time

📌 AUTO-DETECT (Kirim Langsung):

• 📸 FOTO → Analisis metadata & GPS
• 📞 NOMOR (+62xxx) → Cek provider & lokasi
• 🌐 IP (1.1.1.1) → Lacak lokasi + Maps

═══════════════════════════════════
⚠️ HANYA UNTUK PEMBELAJARAN!
📱 Dibuat oleh: {CREATOR}
"""
    await update.message.reply_text(text)

async def ip_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in ALLOWED_CHAT_IDS:
        return
    if not context.args:
        await update.message.reply_text("🌐 Gunakan: /ip 8.8.8.8\n\nContoh:\n/ip 8.8.8.8\n/ip 1.1.1.1\n/ip 103.146.189.131")
        return
    ip_address = context.args[0]
    if not is_valid_ip(ip_address):
        await update.message.reply_text("❌ IP tidak valid!\n\nContoh IP benar:\n• 8.8.8.8\n• 192.168.1.1")
        return
    msg = await update.message.reply_text("🌐 Melacak IP real-time... ⏳")
    try:
        analyzer = IPOSINT(ip_address)
        report = analyzer.generate_report_text()
        await update.message.reply_text(report, disable_web_page_preview=False)
        await msg.delete()
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")
        await msg.delete()

async def scan_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in ALLOWED_CHAT_IDS:
        return

    msg = await update.message.reply_text("📡 Memulai scan jaringan... ⏳\nMohon tunggu 30-60 detik...")

    try:
        scanner = NetworkScanner()
        report = scanner.generate_report()
        await update.message.reply_text(report)
        await msg.delete()
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}\n\nCoba install nmap untuk hasil lebih akurat:\npkg install nmap")
        await msg.delete()

async def analyze_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in ALLOWED_CHAT_IDS:
        return
    msg = await update.message.reply_text("📸 Menganalisis foto... ⏳")
    temp_path = None
    try:
        photo_file = await update.message.photo[-1].get_file()
        temp_path = get_temp_path(chat_id, "photo")
        await photo_file.download_to_drive(temp_path)
        analyzer = PhotoOSINT(temp_path)
        report = analyzer.generate_report_text()
        await update.message.reply_text(report, disable_web_page_preview=False)
        await msg.delete()
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")
        await msg.delete()
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in ALLOWED_CHAT_IDS:
        return
    text = update.message.text.strip()

    if is_valid_ip(text):
        msg = await update.message.reply_text("🌐 Melacak IP real-time... ⏳")
        try:
            analyzer = IPOSINT(text)
            report = analyzer.generate_report_text()
            await update.message.reply_text(report, disable_web_page_preview=False)
            await msg.delete()
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
            await msg.delete()
        return

    if is_valid_phone(text):
        msg = await update.message.reply_text("📞 Menganalisis nomor telepon... ⏳")
        try:
            analyzer = PhoneOSINT(text)
            report = analyzer.generate_report_text()
            await update.message.reply_text(report)
            await msg.delete()
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
            await msg.delete()
        return

# ==================== MAIN ====================
def main():
    print(f"""
    ╔══════════════════════════════════════════════════════════════════╗
    ║     {BOT_NAME.upper()} - OSINT PRO ULTIMATE BOT                     ║
    ║     Dibuat oleh: {CREATOR}                                         ║
    ║     Fitur: Photo + Phone + IP Tracker + Network Scanner + Maps    ║
    ╚══════════════════════════════════════════════════════════════════╝
    """)

    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ ERROR: Ganti BOT_TOKEN dengan token bot Anda!")
        print("   Dapatkan dari @BotFather")
        return

    if ALLOWED_CHAT_IDS == [123456789]:
        print("⚠️ PERINGATAN: Ganti ALLOWED_CHAT_IDS dengan ID Telegram Anda!")
        print("   Cek ID di @userinfobot\n")

    print(f"📁 Direktori kerja: {WORK_DIR}")
    print(f"✅ WORK_DIR siap: {os.path.exists(WORK_DIR)}\n")

    print("📋 SEMUA FITUR OSINT YANG TERSEDIA:")
    print("   1. 📸 Photo OSINT - Analisis metadata & GPS foto + Google Maps")
    print("   2. 📞 Phone OSINT - Analisis nomor telepon (Provider/Lokasi/Timezone)")
    print("   3. 🌐 IP Tracker - Geolokasi IP real-time + Deteksi VPN/Proxy")
    print("   4. 📡 Network Scanner - Scan jaringan + Deteksi Nama Perangkat (5 metode)")
    print("   5. 🗺️ Google Maps Integration - Link langsung ke peta")
    print("")

    try:
        app = Application.builder().token(BOT_TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(CommandHandler("ip", ip_command))
        app.add_handler(CommandHandler("scan", scan_command))
        app.add_handler(CallbackQueryHandler(menu_callback))
        app.add_handler(MessageHandler(filters.PHOTO, analyze_photo))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

        print(f"✅ {BOT_NAME.upper()} Bot berjalan dengan sukses!")
        print("📱 Perintah yang tersedia:")
        print("   • /start - Menu utama interaktif")
        print("   • /help - Bantuan lengkap")
        print("   • /ip 8.8.8.8 - Lacak IP real-time + Maps")
        print("   • /scan - Scan jaringan sendiri (dengan deteksi nama)")
        print("   • Kirim FOTO - Analisis metadata & GPS")
        print("   • Kirim NOMOR (+62xxx) - Auto-detect")
        print("   • Kirim IP - Auto-detect")
        print(f"\n⚠️ HANYA UNTUK PEMBELAJARAN DI LAB!")
        print(f"📱 Dibuat oleh: {CREATOR}")
        print("   Tekan Ctrl+C untuk berhenti\n")

        app.run_polling(allowed_updates=Update.ALL_TYPES)

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
