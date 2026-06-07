# Seedance 2.0 API Client

Client API tích hợp Seedance 2.0 để tạo video AI thông qua API chính thức.

## Cài đặt

```bash
pip install -r requirements.txt
```

## Sử dụng nhanh

```python
import os
from seedance_client import SeedanceAPIClient

# Khởi tạo client với API key (khuyến nghị lấy từ biến môi trường)
client = SeedanceAPIClient(os.environ["ARK_API_KEY"])

# Tạo video
result = client.generate_video(
    prompt="Mô tả nội dung video bạn muốn tạo",
    ratio="16:9",
    resolution="720p",
    duration=10,
    generate_audio=True,
)

task_id = result["id"]

# Đợi video hoàn thành và nhận URL
video_url = client.wait_for_video(task_id)
print(f"Video URL: {video_url}")
```

## Các chức năng có sẵn

✅ `generate_video()` - Gửi yêu cầu tạo video (text-to-video / image-to-video)
✅ `get_task_status()` - Kiểm tra trạng thái task
✅ `wait_for_video()` - Đợi tự động cho đến khi video xong
✅ `list_tasks()` - Lấy danh sách task
✅ `cancel_or_delete_task()` - Cancel task queued hoặc xóa record task

## Tham số hỗ trợ

| Tham số | Giá trị mặc định | Các lựa chọn |
|---------|------------------|--------------|
| `ratio` | `16:9` | 1:1, 16:9, 9:16, 4:3, 3:4 |
| `resolution` | `720p` | 480p, 720p |
| `duration` | `10` | Thường tối đa 15s / task |
| `generate_audio` | `True` | True / False |

## Ví dụ chạy thử

```bash
export ARK_API_KEY="..."
python generate_hopesify_video.py --prompt "Create a vertical 9:16 video..." --ratio 9:16 --duration 10
```
