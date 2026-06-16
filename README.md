# DS200 LAB 5 - People Counting Pipeline

He thong gom 3 server TCP xu ly luong khung hinh camera va dem so nguoi trong moi khung hinh.

## Kien truc

1. `server1_camera.py`: doc camera, video, hoac tao frame gia lap neu may khong co camera. Server nay gui frame dang JPEG base64 qua TCP.
2. `server2_processor.py`: nhan frame, chay OpenCV HOG people detector, tao bounding box cho cac doi tuong `person`, roi gui ket qua sang server luu tru.
3. `server3_storage.py`: nhan ket qua va luu JSON Lines theo partition ngay trong `data/results/date=YYYY-MM-DD/results.jsonl`.
4. `analytics_spark.py`: doc du lieu da luu bang PySpark de tong hop so nguoi theo camera.

Giao thuc truyen du lieu duoc viet theo mau `tcp_example.py`: moi message la mot JSON object ket thuc bang ky tu xuong dong.

## Cai dat

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Neu muon chay phan tong hop du lieu lon bang PySpark:

```bash
pip install -r requirements-bigdata.txt
```

## Chay he thong

Mo 3 terminal theo dung thu tu:

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

Neu khong co webcam, chuong trinh tu tao frame gia lap:

```bash
python server1_camera.py --source 999 --limit 10 --fps 2
```

Co the dung video file:

```bash
python server1_camera.py --source path/to/video.mp4 --limit 100 --fps 10
```

## Ket qua luu tru

Moi dong trong file JSONL co dang:

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

## Phan tich du lieu lon

Du lieu duoc luu theo dinh dang JSONL partition theo ngay, phu hop cho xu ly batch/stream bang cac cong cu du lieu lon. Chay tong hop bang PySpark:

```bash
python analytics_spark.py --input data/results
```

## Commit len GitHub

Thu muc nay can duoc commit len repository GitHub cua sinh vien:

```bash
git add .
git commit -m "Implement distributed people counting pipeline"
git push
```
