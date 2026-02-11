# Sử dụng Python làm base image
FROM python:3.10-slim

# Thiết lập thư mục làm việc trong container
WORKDIR /app

# Copy file requirements (nếu bạn có) hoặc cài đặt thư viện trực tiếp
# Bạn nên tạo file requirements.txt chứa: pandas, psycopg2-binary, sqlalchemy...
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ code vào container
COPY . .

# Lệnh mặc định khi chạy container (ví dụ chạy file main.py)
CMD ["python", "scripts/main.py"]