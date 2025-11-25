import requests
import json
import urllib3
import getpass

# Tắt cảnh báo SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CẤU HÌNH MẶC ĐỊNH ---
# Gán cứng IP Kali ở đây
DEFAULT_URL = "https://192.168.2.28:9200"
DEFAULT_USER = "elastic"

# Cấu hình chung cho tất cả index (Yêu cầu đề tài)
SETTINGS = {
    "number_of_shards": 3,
    "number_of_replicas": 1
}

# Định nghĩa Mapping cho từng Index
INDICES_CONFIG = {
    "qtm17_devices": {
        "mappings": {
            "properties": {
                "device_name": { "type": "text" },
                "brand": { "type": "keyword" },
                "type": { "type": "keyword" },
                "power_usage_w": { "type": "integer" },
                "price": { "type": "double" },
                "release_date": { "type": "date" }
            }
        }
    },
    "qtm17_music": {
        "mappings": {
            "properties": {
                "instrument": { "type": "text" },
                "family": { "type": "keyword" },
                "material": { "type": "text" },
                "is_electric": { "type": "boolean" },
                "price": { "type": "double" }
            }
        }
    },
    "qtm17_vehicles": {
        "mappings": {
            "properties": {
                "model": { "type": "text" },
                "manufacturer": { "type": "keyword" },
                "color": { "type": "keyword" },
                "year": { "type": "integer" },
                "price": { "type": "double" },
                "mileage": { "type": "long" }
            }
        }
    }
}

def get_credentials():
    print("\n--- CẤU HÌNH KẾT NỐI ---")
    
    # Sử dụng luôn mặc định, không hỏi nữa
    url = DEFAULT_URL
    user = DEFAULT_USER
    
    print(f"🔹 Mục tiêu: {url}")
    print(f"🔹 Tài khoản: {user}")

    # Chỉ hỏi mật khẩu
    password = getpass.getpass(f"🔑 Nhập Mật khẩu: ")
    return url, user, password

def main():
    BASE_URL, USER, PASS = get_credentials()
    AUTH = (USER, PASS)

    print(f"\n🔥 BẮT ĐẦU TẠO {len(INDICES_CONFIG)} INDEX...")

    for index_name, config in INDICES_CONFIG.items():
        url = f"{BASE_URL}/{index_name}"
        
        # 1. Xóa nếu đã tồn tại (để làm mới)
        try:
            requests.delete(url, auth=AUTH, verify=False)
            print(f"🗑️  Đã xóa index cũ: {index_name}")
        except: pass

        # 2. Tạo mới
        body = {
            "settings": SETTINGS,
            "mappings": config["mappings"]
        }
        
        try:
            res = requests.put(url, auth=AUTH, json=body, verify=False)
            if res.status_code == 200:
                print(f"✅ TẠO THÀNH CÔNG: {index_name} (3 Shards, 1 Replicas)")
            else:
                print(f"❌ Lỗi tạo {index_name}: {res.text}")
        except Exception as e:
            print(f"❌ Lỗi kết nối: {e}")

    print("\n🎉 Hoàn tất cấu hình!")

if __name__ == "__main__":
    main()
