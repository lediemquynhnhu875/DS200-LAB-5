# DS200 LAB 5 - People Counting Pipeline

Hệ thống gồm 3 server TCP xử lý luồng khung hình camera và đếm số người trong mỗi khung hình.

## Kiến trúc

1. `server1_camera.py`: đọc camera, video, hoặc tạo frame giả lập nếu máy không có camera. Server này gửi frame dạng JPEG base64 qua TCP.
2. `server2_processor.py`: nhận frame, chạy OpenCV HOG people detector, tạo bounding box cho các đối tượng `person`, rồi gửi kết quả sang server lưu trữ.
3. `server3_storage.py`: nhận kết quả và lưu JSON Lines theo partition ngày trong `data/results/date=YYYY-MM-DD/results.jsonl`.
4. `analytics_spark.py`: đọc dữ liệu đã lưu bằng PySpark để tổng hợp số người theo camera.

Giao thức truyền dữ liệu được viết theo mẫu `tcp_example.py`: mỗi message là một JSON object kết thúc bằng ký tự xuống dòng.

## Cài đặt

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Nếu muốn chạy phần tổng hợp dữ liệu lớn bằng PySpark:

```bash
pip install -r requirements-bigdata.txt
```

## Chạy hệ thống

Mở 3 terminal theo đúng thứ tự:

Terminal 1:

```bash
python server3_storage.py
```

Terminal 2:

```bash
python server2_processor.py
```

Terminal 3:

```bash
python server1_camera.py --source 0 --limit 30 --fps 5
```

Nếu không có webcam, chương trình tự tạo frame giả lập:

```bash
python server1_camera.py --source 999 --limit 10 --fps 2
```

Có thể dùng video file:

```bash
python server1_camera.py --source path/to/video.mp4 --limit 100 --fps 10
```

## Kết quả lưu trữ

Mỗi dòng trong file JSONL có dạng:

```json
{
  "type": "detection_result",
  "camera_id": "camera-01",
  "frame_id": 0,
  "people_count": 1,
  "bounding_boxes": [
    {
      "class_name": "person",
      "confidence": 0.82,
      "x": 120,
      "y": 64,
      "width": 80,
      "height": 180
    }
  ]
}
```

## Phân tích dữ liệu lớn

Dữ liệu được lưu theo định dạng JSONL partition theo ngày, phù hợp cho xử lý batch/stream bằng các công cụ dữ liệu lớn. Chạy tổng hợp bằng PySpark:

```bash
python analytics_spark.py --input data/results
```

## Commit lên GitHub

Thư mục này cần được commit lên repository GitHub của sinh viên:

```bash
git add .
git commit -m "Implement distributed people counting pipeline"
git push
```
