# Seedance 2.0 Video Orchestrator

Ứng dụng web tạo video marketing tự động với kiến trúc 2 phần:
- Frontend React + Vite để nhập brief và theo dõi trạng thái task
- Backend FastAPI để điều phối luồng tạo video

## Kiến Trúc

- `frontend/`: giao diện chat để tạo video và theo dõi tiến trình
- `main.py`: FastAPI backend, tạo task và trả trạng thái
- `services/`: các service xử lý theo luồng orchestrator
  - `social_video_generator.py`
  - `video_director.py`
  - `camera_man.py`
  - `orchestrator.py`
- `seedance_client.py`: client gọi Seedance 2.0 API trực tiếp

## Luồng Xử Lý

Người dùng nhập brief → frontend gọi `POST /api/create-video` → backend tạo task → orchestrator chạy tuần tự:
- social-video-generator
- seedance-video-director
- seedance2-camera-man

Frontend poll `GET /api/task/{task_id}` để nhận trạng thái mới nhất.

## Yêu Cầu Môi Trường

Tạo file `.env` ở thư mục gốc với các biến sau:

```env
OPENAI_API_KEY=your-openai-key
DOUBAO_API_KEY=your-doubao-key
DOUBAO_MODEL_ID=doubao-seed-2-0-pro-260215
ARK_API_KEY=your-ark-key
```

- `social-video-generator` dùng `OPENAI_API_KEY`
- `video-director` dùng `DOUBAO_API_KEY` và `DOUBAO_MODEL_ID`
- `camera_man` dùng `ARK_API_KEY`

## Chạy Backend

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

API sẽ chạy tại:
- `http://localhost:8000`
- Swagger docs: `http://localhost:8000/docs`

## Chạy Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend mặc định chạy tại:
- `http://localhost:5173`

## Build Frontend

```bash
cd frontend
npm run build
```

Kết quả build nằm trong `frontend/dist`.

## Deploy Production

### Backend

```bash
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Frontend

1. Set biến môi trường `VITE_API_BASE_URL` cho frontend nếu bạn muốn đổi backend URL.
2. Build frontend:

```bash
cd frontend
npm install
npm run build
```

3. Serve thư mục `frontend/dist` bằng Nginx hoặc static server.

## API Chính

- `POST /api/create-video` - tạo task mới
- `GET /api/task/{task_id}` - lấy trạng thái task
- `GET /api/tasks` - lấy danh sách task gần nhất

## Lưu Ý

- Task state hiện tại được lưu trong memory (`tasks_db`), nên sẽ mất khi restart backend.
- Nếu deploy production thật, nên thay bằng database hoặc Redis.
- Cần đảm bảo các API key trong `.env` hợp lệ để các service gọi model thành công.

## Chạy Nhanh

```bash
# backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000

# frontend
cd frontend
npm install
npm run dev
```
