import requests
import json
import random
import time
import urllib3
import getpass

# Tắt cảnh báo SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CẤU HÌNH MẶC ĐỊNH ---
# Gán cứng IP Kali ở đây
DEFAULT_URL = "https://192.168.2.28:9200"
DEFAULT_USER = "elastic"

# Cấu hình nạp dữ liệu
RECORDS_PER_INDEX = 1000000 # 1 Triệu dòng mỗi index
BATCH_SIZE = 5000

# Dữ liệu mẫu để random (Giữ nguyên)
DATA_POOLS = {
    "devices": {
        "brands": ["Apple", "Samsung", "Sony", "LG", "Dell", "HP", "Panasonic"],
        "types": ["Smartphone", "Laptop", "TV", "Fridge", "Washing Machine", "Headphone"],
        "names": ["Pro", "Max", "Ultra", "Slim", "Gaming", "Smart", "Eco"]
    },
    "music": {
        "families": ["String", "Percussion", "Wind", "Keyboard", "Electronic"],
        "instruments": ["Guitar", "Piano", "Drum", "Violin", "Flute", "Saxophone", "Synthesizer"],
        "materials": ["Wood", "Brass", "Plastic", "Steel", "Gold Plated"]
    },
    "vehicles": {
        "manufacturers": ["Toyota", "Honda", "Ford", "Tesla", "BMW", "Mercedes", "VinFast"],
        "colors": ["Red", "Blue", "Black", "White", "Silver", "Grey"],
        "models": ["Sedan", "SUV", "Truck", "Coupe", "Hatchback", "Convertible"]
    }
}

# Danh sách index cần nạp (Phải khớp tên với file create_indices.py)
TARGET_INDICES = ["qtm17_devices", "qtm17_music", "qtm17_vehicles"]

def get_credentials():
    print("\n--- CẤU HÌNH KẾT NỐI ---")
    
    # Sử dụng luôn mặc định
    url = DEFAULT_URL
    user = DEFAULT_USER
    
    print(f"🔹 Mục tiêu: {url}")
    print(f"🔹 Tài khoản: {user}")

    # Chỉ hỏi mật khẩu
    password = getpass.getpass(f"🔑 Nhập Mật khẩu: ")
    return url, user, password

def generate_doc(index_name, doc_id):
    # Logic chọn dữ liệu (Giữ nguyên)
    if "devices" in index_name:
        d = DATA_POOLS["devices"]
        return {
            "device_name": f"{random.choice(d['brands'])} {random.choice(d['types'])} {random.choice(d['names'])} {doc_id}",
            "brand": random.choice(d['brands']),
            "type": random.choice(d['types']),
            "power_usage_w": random.randint(5, 2000),
            "price": round(random.uniform(100, 3000), 2),
            "release_date": "2024-01-01"
        }
    elif "music" in index_name:
        m = DATA_POOLS["music"]
        return {
            "instrument": f"{random.choice(m['materials'])} {random.choice(m['instruments'])} {doc_id}",
            "family": random.choice(m['families']),
            "material": random.choice(m['materials']),
            "is_electric": bool(random.getrandbits(1)),
            "price": round(random.uniform(50, 5000), 2)
        }
    elif "vehicles" in index_name:
        v = DATA_POOLS["vehicles"]
        return {
            "model": f"{random.choice(v['manufacturers'])} {random.choice(v['models'])} {doc_id}",
            "manufacturer": random.choice(v['manufacturers']),
            "color": random.choice(v['colors']),
            "year": random.randint(1990, 2025),
            "price": round(random.uniform(10000, 100000), 2),
            "mileage": random.randint(0, 200000)
        }
    return {}

def main():
    BASE_URL, USER, PASS = get_credentials()
    AUTH = (USER, PASS)

    print(f"\n🔥 BẮT ĐẦU NẠP DỮ LIỆU: 3 INDEX x {RECORDS_PER_INDEX} BẢN GHI")
    total_start = time.time()

    for index_name in TARGET_INDICES:
        bulk_url = f"{BASE_URL}/{index_name}/_bulk"
        print(f"\n🚀 Đang nạp cho: {index_name}...")
        
        start_time = time.time()
        for i in range(0, RECORDS_PER_INDEX, BATCH_SIZE):
            bulk_data = ""
            for j in range(BATCH_SIZE):
                doc_id = i + j + 1
                meta = { "index": { "_id": str(doc_id) } }
                doc = generate_doc(index_name, doc_id)
                bulk_data += json.dumps(meta) + "\n" + json.dumps(doc) + "\n"
            
            try:
                res = requests.post(
                    bulk_url, auth=AUTH, data=bulk_data, 
                    headers={'Content-Type': 'application/x-ndjson'}, verify=False
                )
                if res.status_code != 200:
                    print(f"❌ Lỗi batch: {res.text[:50]}")
            except Exception as e:
                print(f"❌ Lỗi kết nối: {e}")
                break
            
            # In tiến độ
            percent = ((i + BATCH_SIZE) / RECORDS_PER_INDEX) * 100
            print(f"   >>> Tiến độ: {percent:.1f}%", end='\r')
        
        duration = time.time() - start_time
        print(f"\n✅ Xong {index_name} trong {duration:.2f}s")

    print(f"\n🎉🎉🎉 HOÀN TẤT TOÀN BỘ! Tổng thời gian: {(time.time() - total_start)/60:.2f} phút.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🚫 Dừng.")
