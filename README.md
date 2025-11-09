Dự án Triển khai Elasticsearch Cluster (QTM17)
Đây là dự án triển khai một cụm (cluster) Elasticsearch gồm 3-node (ES-Node-01, 02, 03) trên Docker.

Cluster này được bảo mật hoàn toàn, bao gồm:
- SSL/TLS: Toàn bộ giao tiếp được mã hóa (chạy trên https://)
- Authentication: Yêu cầu tên đăng nhập và mật khẩu.
- Role-Based Access Control (RBAC): Phân quyền truy cập (ví dụ: user dev_user chỉ có quyền đọc).

I. 🚀 Hướng dẫn Cài đặt & Khởi chạy (5 Bước)
Đây là các bước để bạn tự chạy dự án này từ đầu.

Bước 1: Tải dự án về

git clone https://github.com/USER_CUA_BAN/TEN_REPO.git

cd TEN_REPO

Bước 2: Tự tạo Chứng Chỉ SSL

Chạy lệnh để tạo file elastic-certificates.p12:

# 1. Tạo file CA (Tổ chức phát hành chứng chỉ)
sudo docker run --rm -v "$(pwd):/certs" \
  docker.elastic.co/elasticsearch/elasticsearch:8.10.4 \
  /usr/share/elasticsearch/bin/elasticsearch-certutil ca \
  --pass "" \
  --out "/certs/elastic-stack-ca.p12"

# 2. Tạo file Chứng chỉ cho các node
sudo docker run --rm -v "$(pwd):/certs" \
  docker.elastic.co/elasticsearch/elasticsearch:8.10.4 \
  /usr/share/elasticsearch/bin/elasticsearch-certutil cert \
  --ca "/certs/elastic-stack-ca.p12" \
  --ca-pass "" \
  --pass "" \
  --dns es-node-01,es-node-02,es-node-03 \
  --ip 127.0.0.1,172.0.0.1 \
  --out "/certs/elastic-certificates.p12"

Bước 3: Sửa lỗi Phân Quyền File

Cấp quyền cho file cert vừa tạo

sudo chown 1000:1000 elastic-certificates.p12

Bước 4: Khởi động Cluster & Lấy Mật Khẩu

Khởi động cluster và tạo mật khẩu.

# 1. Khởi động 3 node (chạy nền). Sau khi khởi động, đợi 4-5 phút để Cluster khởi động, bầu master và đọc SSL.
sudo docker-compose up -d

# 2. Chạy lệnh tạo mật khẩu tự động
sudo docker exec -it ES-Node-01 /usr/share/elasticsearch/bin/elasticsearch-setup-passwords auto -b -u "https://127.0.0.1:9200"

🔥 QUAN TRỌNG: Lệnh trên sẽ in ra một danh sách mật khẩu. Hãy COPY VÀ LƯU LẠI mật khẩu của user elastic. Đây là user "siêu quản trị" (super-admin).

Bước 5: Tạo Dữ liệu và Phân Quyền

Cluster của bạn đang chạy nhưng vẫn "rỗng". Bạn cần dùng mật khẩu elastic (vừa lấy ở Bước 4) để tạo Index, thêm Dữ liệu, tạo Role và tạo User dev_user.

Chạy 4 lệnh curl dưới đây (nhớ thay PASS_ELASTIC_CUA_BAN bằng mật khẩu bạn vừa lưu):

# 1. Tạo Index (từ file index.json)
curl -k -X PUT "https://localhost:9200/qtm17_products" \
     -u elastic:PASS_ELASTIC_CUA_BAN \
     -H 'Content-Type: application/json' -d '@index.json'

# 2. Thêm Dữ liệu (từ file pull_data.json)
curl -k -X POST "https://localhost:9200/qtm17_products/_bulk" \
     -u elastic:PASS_ELASTIC_CUA_BAN \
     -H 'Content-Type: application/json' --data-binary '@pull_data.json'

# 3. Tạo Role (từ file role_reader.json)
curl -k -X POST "https://localhost:9200/_security/role/qtm_reader" \
     -u elastic:PASS_ELASTIC_CUA_BAN \
     -H 'Content-Type: application/json' -d '@role_reader.json'

# 4. Tạo User 'dev_user' (từ file user_dev.json)
Thay đổi tên user: /user/ ____ đổi tên ở đây
Thay password trong file user_dev.json
curl -k -X POST "https://localhost:9200/_security/user/dev_user" \
     -u elastic:PASS_ELASTIC_CUA_BAN \
     -H 'Content-Type: application/json' -d '@user_dev.json'

🎉 Cluster của bạn đã sẵn sàng để sử dụng!

II. ⌨️ Cách sử dụng
Bạn có 2 cách để tương tác với cluster:

Cách 1: Dùng Script (Dễ nhất)

Dự án này có một script search.sh để chạy search .

# 1. Cấp quyền chạy script (chỉ làm 1 lần)
chmod +x search.sh

# 2. Chạy tìm kiếm!
./search.sh <phuong_thuc> <truong> <gia_tri>

Script sẽ tự động hỏi bạn Username và Password. Bạn có thể dùng:

User: dev_user
Pass: (Mật khẩu trong file user_dev.json của bạn, ví dụ: toan1234)

Cách 2: Dùng curl (Kiểu Quản trị)

Kiểm tra sức khỏe cluster bằng user elastic (dùng pass bạn đã lưu ở Bước 4):

curl -k "https://localhost:9200/_cluster/health?pretty" -u elastic:PASS_ELASTIC_CUA_BAN
(Kết quả mong đợi: "status" : "green")

1. Match Query (Tìm kiếm toàn văn - Full-text search)

Đây là kiểu tìm kiếm "Google". Nó dùng để tìm kiếm văn bản, có phân tích từ (ví dụ: tìm "laptop" sẽ thấy "High Performance Laptop"). Nó hoạt động tốt nhất trên các trường text (như product_name).

+ <TEN_USER> : Trong đồ án này là dev_user (có thể thay đổi ở bước tạo user ở trên)
+ <MAT_KHAU> : Trong đồ án này là toan1234 (có thể thay đổi ở bước tạo user ở trên)

curl -k "https://localhost:9200/qtm17_products/_search?pretty" \
     -u <TEN_USER>:<MAT_KHAU> \
     -H 'Content-Type: application/json' -d'
{
  "query": {
    "match": {
      "<TRUONG_CAN_TIM>": "<GIA_TRI_BAN_MUON_TIM>"
    }
  }
}

2. Term Query (Tìm kiếm chính xác)

Đây là kiểu tìm kiếm chính xác, không phân tích từ. Nó dùng để lọc (filter) các giá trị. Nó hoạt động tốt nhất trên các trường keyword (như category).

+ <TEN_USER> : Trong đồ án này là dev_user (có thể thay đổi ở bước tạo user ở trên)
+ <MAT_KHAU> : Trong đồ án này là toan1234 (có thể thay đổi ở bước tạo user ở trên)

curl -k "https://localhost:9200/qtm17_products/_search?pretty" \
     -u <TEN_USER>:<MAT_KHAU> \
     -H 'Content-Type: application/json' -d'
{
  "query": {
    "term": {
      "<TRUONG_CAN_LOC>": "<GIA_TRI_CHINH_XAC>"
    }
  }
}
'

3. Boolean Query (Kết hợp AND/OR/NOT)
Đây là loại kết hợp nhiều truy vấn lại với nhau.

- must: Tương đương với AND (Tất cả điều kiện phải đúng).
- should: Tương đương với OR (Một trong các điều kiện đúng).
- must_not: Tương đương với NOT (Điều kiện không được đúng).

+ <TEN_USER> : Trong đồ án này là dev_user (có thể thay đổi ở bước tạo user ở trên)
+ <MAT_KHAU> : Trong đồ án này là toan1234 (có thể thay đổi ở bước tạo user ở trên)

curl -k "https://localhost:9200/qtm17_products/_search?pretty" \
     -u <TEN_USER>:<MAT_KHAU> \
     -H 'Content-Type: application/json' -d'
{
  "query": {
    "bool": {
      "must": [
        { "term": { "<TRUONG_DIEU_KIEN_1>": "<GIA_TRI_1>" } }
      ],
      "must_not": [
        { "term": { "<TRUONG_DIEU_KIEN_2>": "<GIA_TRI_2>" } }
      ],
      "should": [
        { "match": { "<TRUONG_DIEU_KIEN_3>": "<GIA_TRI_3>" } }
      ]
    }
  }
}
'

Không cần thiết phải đầy đủ các trường must - must_not - should ( có thể chọn 1 trong 3 hoặc chọn hết )

4. Aggregation (Tổng hợp: sum, avg, group by)
"Aggregation" (hay "aggs") là cách Elasticsearch thực hiện thống kê.

Lưu ý: Chúng ta thêm "size": 0 vì chúng ta không quan tâm đến kết quả tìm kiếm (hits), chúng ta chỉ muốn xem kết quả thống kê (aggregations).

+ <TEN_USER> : Trong đồ án này là dev_user (có thể thay đổi ở bước tạo user ở trên)
+ <MAT_KHAU> : Trong đồ án này là toan1234 (có thể thay đổi ở bước tạo user ở trên)

curl -k "https://localhost:9200/qtm17_products/_search?pretty" \
     -u <TEN_USER>:<MAT_KHAU> \
     -H 'Content-Type: application/json' -d'
{
  "size": 0,
  "aggs": {
    "<TEN_NHOM_BAN_DAT>": {
      "terms": { "field": "<TRUONG_DE_GROUP_BY>" },
      "aggs": {
        "<TEN_PHEP_TINH_TONG>": {
          "sum": { "field": "<TRUONG_DE_TINH_TONG>" }
        },
        "<TEN_PHEP_TINH_TRUNG_BINH>": {
          "avg": { "field": "<TRUONG_DE_TINH_TRUNG_BINH>" }
        }
      }
    }
  }
}
'

III. 🛑 Dọn dẹp
Để dừng cluster (giữ dữ liệu):

sudo docker-compose down

Để dừng và XÓA SẠCH MỌI DỮ LIỆU/MẬT KHẨU (làm lại từ đầu):

sudo docker-compose down -v
