"""Seedance 2.0 Camera Man service - extracted from seedance2-camera-man SKILL.md"""
from typing import Dict, Any, List
import asyncio
import os
import time
import requests
import concurrent.futures
from dotenv import load_dotenv

load_dotenv()

class SeedanceCameraMan:
    """Calls Seedance 2.0 API directly to generate the final video from prepared assets"""
    
    DEFAULT_BASE_URL = "https://ark.ap-southeast.bytepluses.com/api/v3/contents/generations"
    
    def __init__(self):
        self.api_key = os.getenv("ARK_API_KEY")
        if not self.api_key:
            raise ValueError("ARK_API_KEY environment variable not configured")
        self.base_url = self.DEFAULT_BASE_URL.rstrip("/")
        self.timeout_s = 120
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)
    
    def _raise_for_api_error(self, response: requests.Response) -> None:
        if 200 <= response.status_code < 300:
            return
        try:
            body = response.json()
        except Exception:
            body = {"raw": response.text}
        status = response.status_code
        if status in {401, 403}:
            raise PermissionError(f"Lỗi xác thực/quyền truy cập (HTTP {status}). Kiểm tra ARK_API_KEY. Response: {body}")
        if status == 429:
            raise RuntimeError(f"Quá tải / rate limit (HTTP 429). Thử lại sau. Response: {body}")
        raise ValueError(f"Lỗi API (HTTP {status}). Response: {body}")
    
    def _generate_video_sync(self, storyboard: str, ratio: str, duration: int, image_urls: List[str], return_last_frame: bool) -> Dict[str, Any]:
        """Sync version of generate_video for thread pool"""
        content = [{"type": "text", "text": str(storyboard)}]
        for img in image_urls:
            content.append({"type": "image_url", "image_url": {"url": img}, "role": "reference_image"})
        
        payload = {
            "model": "dreamina-seedance-2-0-260128",
            "content": content,
            "ratio": ratio,
            "resolution": "1080p",
            "duration": duration,
            "generate_audio": True,
            "return_last_frame": return_last_frame,
            "execution_expires_after": 172800
        }
        
        response = requests.post(
            f"{self.base_url}/tasks",
            headers=self.headers,
            json=payload,
            timeout=self.timeout_s
        )
        self._raise_for_api_error(response)
        return response.json()
    
    def _wait_for_video_sync(self, task_id: str, poll_interval: int = 10, timeout: int = 1200) -> str:
        """Sync version of wait_for_video for thread pool"""
        start_time = time.time()
        last_status = None
        
        while True:
            elapsed = int(time.time() - start_time)
            if elapsed > timeout:
                raise TimeoutError(f"Timeout sau {timeout//60} phút. Task vẫn đang xử lý: {task_id}")
            
            response = requests.get(
                f"{self.base_url}/tasks/{task_id}",
                headers=self.headers,
                timeout=self.timeout_s
            )
            self._raise_for_api_error(response)
            status = response.json()
            current_status = status.get("status") or status.get("data", {}).get("status", "UNKNOWN")
            
            if current_status != last_status:
                last_status = current_status
                print(f"[Camera Man] [{elapsed:4}s] Trạng thái mới: {current_status}")
            
            if current_status in {"succeeded", "SUCCESS"}:
                content = status.get("content") or status.get("data", {}).get("content") or {}
                video_url = content.get("video_url")
                if video_url:
                    return video_url
                outputs = status.get("output") or status.get("data", {}).get("output") or []
                if outputs and isinstance(outputs, list) and isinstance(outputs[0], dict) and "url" in outputs[0]:
                    return outputs[0]["url"]
                raise Exception("Không tìm thấy video_url trong kết quả")
            
            if current_status in {"failed", "FAILED", "error"}:
                error_obj = status.get("error") or status.get("data", {}).get("error") or {}
                msg = error_obj.get("message") or "Lỗi không xác định"
                raise Exception(f"Tạo video thất bại: {msg}")
            
            time.sleep(poll_interval)
    
    def _generate_long_video_sync(self, storyboard: str, ratio: str, total_duration: int, image_urls: List[str]) -> List[Dict[str, Any]]:
        """Sync version of generate_long_video"""
        import math
        segment_duration = 15
        num_segments = math.ceil(total_duration / segment_duration)
        print(f"[Camera Man] Tổng thời lượng {total_duration}s → chia thành {num_segments} segment mỗi đoạn {segment_duration}s")
        
        segments_result = []
        previous_last_frame = None
        
        for seg_idx in range(num_segments):
            print(f"[Camera Man] Đang xử lý segment {seg_idx+1}/{num_segments}")
            current_images = image_urls.copy() if image_urls else []
            if previous_last_frame is not None:
                print(f"[Camera Man] Sử dụng last frame của segment trước")
                current_images.insert(0, previous_last_frame)
            
            task_resp = self._generate_video_sync(
                storyboard=storyboard,
                ratio=ratio,
                duration=segment_duration,
                image_urls=current_images,
                return_last_frame=True
            )
            task_id = task_resp["id"]
            video_url = self._wait_for_video_sync(task_id)
            
            # Get last frame
            status_resp = requests.get(f"{self.base_url}/tasks/{task_id}", headers=self.headers, timeout=self.timeout_s)
            status_data = status_resp.json()
            content = status_data.get("content") or status_data.get("data", {}).get("content") or {}
            last_frame_url = content.get("last_frame_url")
            
            segments_result.append({
                "segment_index": seg_idx,
                "task_id": task_id,
                "video_url": video_url,
                "last_frame_url": last_frame_url
            })
            previous_last_frame = last_frame_url
            print(f"[Camera Man] Segment {seg_idx+1} hoàn thành")
        
        return segments_result
    
    async def generate_video(self, director_output: Dict[str, Any], brief: Dict[str, Any]) -> Dict[str, Any]:
        """Generate final video using Seedance 2.0 API directly with full error handling"""
        api_payload = director_output.get("seedance_api_payload")
        if not api_payload:
            raise ValueError("Missing seedance_api_payload from director output")
        
        try:
            video_duration = int(brief.get("duration", 15))
            storyboard = api_payload.get("storyboard", "")
            ratio = brief.get("ratio", "9:16")
            product_images = brief.get("product_images", [])
            
            if video_duration > 15:
                # Run in thread pool to avoid blocking FastAPI event loop
                segments = await asyncio.get_event_loop().run_in_executor(
                    self.executor,
                    self._generate_long_video_sync,
                    storyboard,
                    ratio,
                    video_duration,
                    product_images
                )
                return {
                    "success": True,
                    "video_url": segments[-1].get("video_url", "") if segments else "",
                    "duration": video_duration,
                    "segments_generated": len(segments),
                    "segment_urls": [s["video_url"] for s in segments]
                }
            else:
                # Chạy API call trong thread riêng
                task = await asyncio.get_event_loop().run_in_executor(
                    self.executor,
                    self._generate_video_sync,
                    storyboard,
                    ratio,
                    video_duration,
                    product_images,
                    api_payload.get("return_last_frame", False)
                )
                # Đợi video hoàn thành - cũng chạy trong thread
                video_url = await asyncio.get_event_loop().run_in_executor(
                    self.executor,
                    self._wait_for_video_sync,
                    task["id"]
                )
                return {
                    "success": True,
                    "video_url": video_url or "",
                    "duration": video_duration,
                    "segments_generated": 1
                }
            
        except Exception as e:
            print(f"[ERROR] Camera Man: {str(e)}")
            raise
