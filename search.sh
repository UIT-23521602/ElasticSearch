#!/bin/bash

# --- CẤU HÌNH SẴN ---
URL="https://localhost:9200/qtm17_products/_search?pretty"
# --------------------

# Hàm in hướng dẫn (khi nhập sai)
print_help() {
  echo "❌ Lỗi: Sai cú pháp."
  echo ""
  echo "Cách dùng: ./search.sh <phuong_thuc> <truong> <gia_tri>"
  echo ""
  echo "Ví dụ:"
  echo "  ./search.sh match product_name guide"
  echo "  ./search.sh term category electronics"
  echo "  ./search.sh price_gt price 30"
}

# 1. Kiểm tra xem có đủ 3 tham số (tham số tìm kiếm) không
if [ "$#" -ne 3 ]; then
  print_help
  exit 1
fi

# --- PHẦN HỎI USER/PASS ---
# Yêu cầu nhập User
echo -n "Nhập Username Elasticsearch: "
read USER

# Yêu cầu nhập Pass (ẩn đi) cho User vừa nhập
echo -n "Nhập mật khẩu cho user '$USER': "
read -s PASS
echo "" # Thêm một dòng mới sau khi gõ pass
# ---------------------------

# 2. Gán tham số vào các biến cho dễ đọc
METHOD="$1"
FIELD="$2"
VALUE="$3"

JSON_QUERY=""

# 3. Chọn cách tìm kiếm (JSON query) dựa trên phương thức
case "$METHOD" in
  "match")
    JSON_QUERY=$(printf '{"query":{"match":{"%s":"%s"}}}' "$FIELD" "$VALUE")
    ;;
  
  "term")
    JSON_QUERY=$(printf '{"query":{"term":{"%s":"%s"}}}' "$FIELD" "$VALUE")
    ;;
  
  "price_gt")
    JSON_QUERY=$(printf '{"query":{"range":{"%s":{"gt":%s}}}}' "$FIELD" "$VALUE")
    ;;
  
  *)
    echo "❌ Lỗi: Phương thức '$METHOD' không được hỗ trợ."
    print_help
    exit 1
    ;;
esac

# 4. In ra và chạy lệnh curl cuối cùng
echo "🔍 Đang tìm kiếm (User: $USER): $METHOD $FIELD = $VALUE"
echo "------------------------------------------------"
curl -k "$URL" \
     -u "$USER:$PASS" \
     -H 'Content-Type: application/json' \
     -d "$JSON_QUERY"
