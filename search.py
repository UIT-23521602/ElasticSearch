import requests
import time
import json
import urllib3
import getpass
import os

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# Tắt cảnh báo SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CẤU HÌNH MẶC ĐỊNH ---
DEFAULT_IP = "192.168.2.28"
DEFAULT_INDEX = "qtm17_devices"
DEFAULT_USER = "elastic"

def get_connection_info():
    print("\n🔐 --- CẤU HÌNH KẾT NỐI ---")
    
    input_user = input(f"1. Nhập User (Mặc định {DEFAULT_USER}): ").strip()
    user = input_user if input_user else DEFAULT_USER

    password = getpass.getpass(f"2. Nhập Mật khẩu cho user '{user}': ")

    ip_input = input(f"3. Nhập IP Node (Mặc định {DEFAULT_IP}): ").strip()
    ip = ip_input if ip_input else DEFAULT_IP

    index_input = input(f"4. Nhập Tên Index muốn tìm (Mặc định {DEFAULT_INDEX}): ").strip()
    index_name = index_input if index_input else DEFAULT_INDEX
    
    full_url = f"https://{ip}:9200/{index_name}/_search"
    
    print(f"\n🎯 Target: {full_url}")
    return full_url, user, password

def execute_request(url, user, password, query_body, query_type="search", extra_fields=[]):
    print(f"\n🚀 Đang gửi truy vấn...")
    
    start_time = time.time()
    
    try:
        response = requests.get(
            url, 
            auth=(user, password), 
            json=query_body, 
            verify=False 
        )
        
        end_time = time.time()
        total_time = (end_time - start_time) * 1000

        if response.status_code == 200:
            result = response.json()
            es_took = result['took']
            
            print("-" * 70)
            print(f"✅ KẾT QUẢ ({query_type}):")
            
            # 1. Nếu là Aggregation
            if "aggregations" in result:
                aggs = result['aggregations']
                if 'my_buckets' in aggs:
                    print(f"{'NHÓM (KEY)':<20} | {'SỐ LƯỢNG':<10} | {'THỐNG KÊ'}")
                    print("-" * 70)
                    for bucket in aggs['my_buckets']['buckets']:
                        metric_val = "N/A"
                        if 'my_metric' in bucket:
                            metric_val = round(bucket['my_metric']['value'], 2)
                        print(f"{bucket['key']:<20} | {bucket['doc_count']:<10} | {metric_val}")
                else:
                    print(json.dumps(aggs, indent=2))

            # 2. Nếu là Search thường
            else:
                hits = result['hits']['hits']
                total = result['hits']['total']['value']
                relation = result['hits']['total']['relation']
                total_str = f"{total}" if relation == "eq" else f">={total}"
                
                print(f"👉 Tìm thấy: {bcolors.OKCYAN}{total_str}{bcolors.ENDC} bản ghi")
                print("-" * 70)
                
                if len(hits) > 0:
                    for item in hits[:5]: 
                        source = item['_source']
                        name = source.get('device_name') or source.get('product_name') or source.get('model') or source.get('instrument') or "N/A"
                        
                        # --- TẠO CHUỖI HIỂN THỊ CÁC TRƯỜNG ĐÃ TÌM ---
                        extra_info_list = []
                        for f in extra_fields:
                            val = source.get(f, 'N/A')
                            extra_info_list.append(f"{f}: {bcolors.OKBLUE}{val}{bcolors.ENDC}")
                        
                        extra_info_str = " | ".join(extra_info_list)

                        # --- XỬ LÝ HIGHLIGHT ---
                        highlight_text = ""
                        if 'highlight' in item:
                            for field, fragments in item['highlight'].items():
                                raw_text = fragments[0]
                                colored_text = raw_text.replace("<em>", f"{bcolors.FAIL}{bcolors.BOLD}").replace("</em>", bcolors.ENDC)
                                highlight_text = f" 🔥 {colored_text}" 
                                break
                        
                        print(f"ID: {item['_id']} | {name}")
                        if extra_info_str:
                            print(f"   ℹ️  Chi tiết: {extra_info_str}")
                        if highlight_text:
                            print(f"   ↳ MATCH:{highlight_text}") 
                        print("-" * 30)
                else:
                    print("(Không có dữ liệu hiển thị)")

            print("-" * 70)
            print(f"⏱️  THỜI GIAN: ES: {bcolors.OKGREEN}{es_took} ms{bcolors.ENDC} | Tổng: {bcolors.OKGREEN}{total_time:.2f} ms{bcolors.ENDC}")
            print("-" * 70)
            
        else:
            print(f"❌ Lỗi: {response.status_code} - {response.text[:100]}")

    except Exception as e:
        print(f"❌ Lỗi kết nối: {e}")

# --- CÁC HÀM NHẬP LIỆU ---

def mode_match(url, user, password):
    print("\n--- 1. MATCH QUERY (Tìm kiếm toàn văn) ---")
    field = input("Nhập tên trường (Enter dùng 'device_name'): ").strip() or "device_name"
    keyword = input(f"Nhập từ khóa tìm trong '{field}': ").strip()
    
    query = { 
        "track_total_hits": True,
        "query": { "match": { field: keyword } } 
    }
    execute_request(url, user, password, query, "Match", extra_fields=[field])

def mode_term(url, user, password):
    print("\n--- 2. TERM QUERY (Tìm chính xác) ---")
    field = input("Nhập tên trường (Enter dùng 'brand'): ").strip() or "brand"
    keyword = input(f"Nhập giá trị chính xác cho '{field}': ").strip()
    
    query = { 
        "track_total_hits": True,
        "query": { "term": { field: keyword } } 
    }
    execute_request(url, user, password, query, "Term", extra_fields=[field])

# --- HÀM BOOLEAN ĐƯỢC NÂNG CẤP ---
def mode_bool(url, user, password):
    print("\n--- 3. BOOLEAN QUERY (Tùy chỉnh linh hoạt) ---")
    print("Xây dựng câu truy vấn kết hợp 2 điều kiện.")
    
    # Khởi tạo cấu trúc query rỗng
    bool_query_content = {}

    # --- Điều kiện 1: Term Query ---
    print(f"\n{bcolors.OKBLUE}[Điều kiện 1 - Tìm chính xác (Term)]{bcolors.ENDC}")
    f1 = input("   Tên trường (VD: brand): ").strip() or "brand"
    v1 = input(f"   Giá trị cho '{f1}': ").strip()
    
    print("   Loại kết hợp cho điều kiện 1:")
    print("   1. MUST (Bắt buộc có - AND)")
    print("   2. SHOULD (Nên có - OR)")
    print("   3. MUST_NOT (Không được có - NOT)")
    print("   4. FILTER (Lọc - Không tính điểm)")
    type1 = input("   👉 Chọn (1-4) [Mặc định 1]: ").strip()
    
    key1 = "must"
    if type1 == '2': key1 = "should"
    elif type1 == '3': key1 = "must_not"
    elif type1 == '4': key1 = "filter"
    
    # Thêm vào query
    if key1 not in bool_query_content: bool_query_content[key1] = []
    bool_query_content[key1].append({ "term": { f1: v1 } })

    # --- Điều kiện 2: Range Query ---
    print(f"\n{bcolors.OKBLUE}[Điều kiện 2 - Tìm theo phạm vi (Range)]{bcolors.ENDC}")
    f2 = input("   Tên trường (VD: price): ").strip() or "price"
    op = input("   Toán tử (gt/lt/gte/lte) (VD: lt): ").strip() or "lt"
    v2 = input(f"   Giá trị so sánh cho '{f2}': ").strip()
    
    print("   Loại kết hợp cho điều kiện 2:")
    print("   1. FILTER (Lọc - Không tính điểm - Nhanh)")
    print("   2. MUST (Bắt buộc - Có tính điểm)")
    print("   3. MUST_NOT (Cấm - Loại trừ)")
    print("   4. SHOULD (Nên có - Tăng điểm)")
    type2 = input("   👉 Chọn (1-4) [Mặc định 1]: ").strip()

    key2 = "filter"
    if type2 == '2': key2 = "must"
    elif type2 == '3': key2 = "must_not"
    elif type2 == '4': key2 = "should"

    # Thêm vào query
    if key2 not in bool_query_content: bool_query_content[key2] = []
    bool_query_content[key2].append({ "range": { f2: { op: v2 } } })

    # Tạo JSON hoàn chỉnh
    query = {
        "track_total_hits": True,
        "query": {
            "bool": bool_query_content
        }
    }
    
    desc = f"Boolean ({key1} + {key2})"
    execute_request(url, user, password, query, desc, extra_fields=[f1, f2])

def mode_aggs(url, user, password):
    print("\n--- 4. AGGREGATION (Thống kê) ---")
    
    gf = input("1. Group By trường (VD: brand): ").strip() or "brand"
    mt = input("2. Phép tính (avg/sum) (VD: avg): ").strip() or "avg"
    mf = input("3. Trên trường số liệu (VD: price): ").strip() or "price"

    query = {
        "size": 0,
        "aggs": {
            "my_buckets": {
                "terms": { "field": gf },
                "aggs": {
                    "my_metric": { mt: { "field": mf } }
                }
            }
        }
    }
    execute_request(url, user, password, query, "Aggregation")

def mode_fuzzy(url, user, password):
    print("\n--- 5. FUZZY SEARCH (Tìm sai chính tả & Highlight) ---")
    field = input("Nhập tên trường (Enter dùng 'device_name'): ").strip() or "device_name"
    keyword = input(f"Nhập từ khóa SAI CHÍNH TẢ (VD: laptpo): ").strip()
    
    query = {
        "track_total_hits": True,
        "query": {
            "match": {
                field: {
                    "query": keyword,
                    "fuzziness": "AUTO"
                }
            }
        },
        "highlight": {
            "fields": { field: {} }
        }
    }
    execute_request(url, user, password, query, "Fuzzy & Highlight", extra_fields=[field])

# --- MAIN ---
if __name__ == "__main__":
    t_url, t_user, t_pass = get_connection_info()
    
    while True:
        print("\n====== MENU TÌM KIẾM ======")
        print("1. Match Query")
        print("2. Term Query")
        print("3. Boolean Query")
        print("4. Aggregation")
        print("5. Fuzzy & Highlight")
        print("0. Thoát (hoặc đổi Cấu hình)")
        
        choice = input("👉 Chọn chức năng (0-5): ").strip()
        
        if choice == '1': mode_match(t_url, t_user, t_pass)
        elif choice == '2': mode_term(t_url, t_user, t_pass)
        elif choice == '3': mode_bool(t_url, t_user, t_pass)
        elif choice == '4': mode_aggs(t_url, t_user, t_pass)
        elif choice == '5': mode_fuzzy(t_url, t_user, t_pass)
        elif choice == '0':
            reconfig = input("Bạn muốn thoát hẳn (y) hay đổi Cấu hình (n)? (y/n): ").lower()
            if reconfig == 'n':
                t_url, t_user, t_pass = get_connection_info()
            else:
                print("👋 Tạm biệt!")
                break
        else: print("Sai chức năng!")
