import requests
import time
import base64
import mimetypes
import os
from typing import Optional, Dict, Any, List


class SeedanceAPIClient:
    """
    Client API cho Seedance 2.0 (ModelArk Video Generation API)
    Tài liệu: https://docs.byteplus.com/en/docs/ModelArk/1520757
    """
    
    DEFAULT_BASE_URL = "https://ark.ap-southeast.bytepluses.com/api/v3/contents/generations"
    
    def __init__(self, api_key: str, base_url: Optional[str] = None, timeout_s: int = 120):
        self.api_key = api_key
        self.base_url = (base_url or self.DEFAULT_BASE_URL).rstrip("/")
        self.timeout_s = timeout_s
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    @staticmethod
    def _guess_mime_type(file_path: str) -> str:
        mime, _ = mimetypes.guess_type(file_path)
        if mime:
            return mime
        ext = os.path.splitext(file_path)[1].lower().lstrip(".")
        if ext in {"jpg", "jpeg"}:
            return "image/jpeg"
        if ext in {"png"}:
            return "image/png"
        if ext in {"webp"}:
            return "image/webp"
        if ext in {"bmp"}:
            return "image/bmp"
        if ext in {"tiff", "tif"}:
            return "image/tiff"
        if ext in {"gif"}:
            return "image/gif"
        if ext in {"heic"}:
            return "image/heic"
        if ext in {"heif"}:
            return "image/heif"
        if ext in {"wav"}:
            return "audio/wav"
        if ext in {"mp3"}:
            return "audio/mpeg"
        return "application/octet-stream"

    @staticmethod
    def _validate_file_size(file_path: str, max_bytes: int, label: str) -> None:
        size = os.path.getsize(file_path)
        if size > max_bytes:
            raise ValueError(f"{label} quá lớn: {size / (1024 * 1024):.2f} MB (giới hạn {max_bytes / (1024 * 1024):.2f} MB)")

    def file_to_data_uri(self, file_path: str, *, max_mb: int) -> str:
        self._validate_file_size(file_path, max_mb * 1024 * 1024, os.path.basename(file_path))
        mime = self._guess_mime_type(file_path)
        if mime.startswith("image/"):
            fmt = mime.split("/", 1)[1].lower()
            if fmt == "jpg":
                fmt = "jpeg"
            prefix = f"data:image/{fmt};base64,"
        elif mime.startswith("audio/"):
            fmt = mime.split("/", 1)[1].lower()
            prefix = f"data:audio/{fmt};base64,"
        else:
            raise ValueError(f"Định dạng file không hỗ trợ để encode Base64: {mime}")

        with open(file_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
        return prefix + encoded

    def generate_video(
        self,
        prompt: str,
        ratio: str = "16:9",
        resolution: str = "720p",
        duration: int = 10,
        generate_audio: bool = True,
        image_urls: Optional[List[str]] = None,
        image_data_uris: Optional[List[str]] = None,
        image_items: Optional[List[Dict[str, Any]]] = None,
        audio_urls: Optional[List[str]] = None,
        audio_data_uris: Optional[List[str]] = None,
        audio_items: Optional[List[Dict[str, Any]]] = None,
        model: str = "dreamina-seedance-2-0-260128",
        safety_identifier: Optional[str] = None,
        callback_url: Optional[str] = None,
        return_last_frame: bool = False,
        service_tier: str = "default",
        execution_expires_after: int = 172800,
        seed: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Tạo task video generation (Seedance 2.0).
        
        Args:
            prompt: Mô tả nội dung video
            ratio: Tỷ lệ khung hình (1:1, 16:9, 9:16, 4:3, 3:4)
            resolution: Độ phân giải (480p, 720p, 1080p)
            duration: Thời lượng video (thường tối đa 15s; nếu cần dài hơn hãy chia segment)
            generate_audio: Video có âm thanh đồng bộ theo prompt
            image_urls: Danh sách URL ảnh tham chiếu (public URL)
            image_data_uris: Danh sách ảnh Base64 data URI (data:image/<fmt>;base64,...)
            audio_urls: Danh sách URL audio tham chiếu (public URL)
            audio_data_uris: Danh sách audio Base64 data URI (data:audio/<fmt>;base64,...)
            model: Model ID (ví dụ: dreamina-seedance-2-0-260128)
            
        Returns:
            Phản hồi API (thường chứa id + status)
        """
        if "aspect_ratio" in kwargs and ratio == "16:9":
            ratio = kwargs.pop("aspect_ratio")

        if duration > 15:
            import warnings
            warnings.warn("duration > 15s: Sẽ tự động chia thành nhiều segment 15s. Để kiểm soát tốt hơn hãy dùng method generate_long_video()")

        content: List[Dict[str, Any]] = []
        
        content.append({
            "type": "text",
            "text": prompt
        })
        
        if image_items:
            for item in image_items:
                url = item.get("url")
                role = item.get("role")
                if not url:
                    raise ValueError("image_items yêu cầu field 'url'")
                obj: Dict[str, Any] = {"type": "image_url", "image_url": {"url": url}}
                if role:
                    obj["role"] = role
                content.append(obj)
        else:
            for img in (image_urls or []):
                content.append({"type": "image_url", "image_url": {"url": img}, "role": "reference_image"})
            for img in (image_data_uris or []):
                content.append({"type": "image_url", "image_url": {"url": img}, "role": "reference_image"})

        if audio_items:
            for item in audio_items:
                url = item.get("url")
                role = item.get("role", "reference_audio")
                if not url:
                    raise ValueError("audio_items yêu cầu field 'url'")
                content.append({"type": "audio_url", "audio_url": {"url": url}, "role": role})
        else:
            for aud in (audio_urls or []):
                content.append({"type": "audio_url", "audio_url": {"url": aud}, "role": "reference_audio"})
            for aud in (audio_data_uris or []):
                content.append({"type": "audio_url", "audio_url": {"url": aud}, "role": "reference_audio"})
        
        payload = {
            "model": model,
            "content": content,
            "ratio": ratio,
            "resolution": resolution,
            "duration": duration,
            "generate_audio": generate_audio,
            "return_last_frame": return_last_frame,
            "execution_expires_after": execution_expires_after,
            **kwargs,
        }
        if safety_identifier is not None:
            payload["safety_identifier"] = safety_identifier
        if callback_url is not None:
            payload["callback_url"] = callback_url
        if seed is not None:
            payload["seed"] = seed
        
        response = requests.post(
            f"{self.base_url}/tasks",
            headers=self.headers,
            json=payload,
            timeout=self.timeout_s,
        )
        self._raise_for_api_error(response)
        return response.json()

    @staticmethod
    def _raise_for_api_error(response: requests.Response) -> None:
        if 200 <= response.status_code < 300:
            return
        try:
            body = response.json()
        except Exception:
            body = {"raw": response.text}

        status = response.status_code
        if status in {401, 403}:
            raise PermissionError(f"Lỗi xác thực/quyền truy cập (HTTP {status}). Kiểm tra ARK_API_KEY và quyền model. Response: {body}")
        if status == 429:
            raise RuntimeError(f"Quá tải / rate limit (HTTP 429). Thử lại sau, hoặc giảm tần suất poll. Response: {body}")
        raise ValueError(f"Lỗi API (HTTP {status}). Response: {body}")
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Kiểm tra trạng thái task tạo video
        
        Args:
            task_id: ID của task từ generate_video()
            
        Returns:
            Thông tin chi tiết trạng thái, kết quả video nếu hoàn thành
        """
        response = requests.get(
            f"{self.base_url}/tasks/{task_id}",
            headers=self.headers,
            timeout=self.timeout_s,
        )
        self._raise_for_api_error(response)
        return response.json()
    
    def wait_for_video(
        self,
        task_id: str,
        poll_interval: int = 10,
        timeout: int = 1200
    ) -> Optional[str]:
        """
        ✅ Đợi liên tục cho đến khi video được tạo xong
        Không ngắt kết nối, duy trì theo dõi task cho đến khi hoàn thành hoặc timeout
        
        Args:
            task_id: ID của task
            poll_interval: Thời gian chờ giữa các lần kiểm tra (giây)
            timeout: Thời gian tối đa chờ (giây) - mặc định 20 phút
            
        Returns:
            URL video nếu thành công
        """
        start_time = time.time()
        last_status = None
        retry_count = 0
        
        print(f"\n🔔 Bắt đầu theo dõi task: {task_id}")
        print(f"⏱️  Thời gian chờ tối đa: {timeout//60} phút")
        print("="*60)
        
        while True:
            elapsed = int(time.time() - start_time)
            
            if elapsed > timeout:
                raise TimeoutError(f"⏰ Timeout sau {timeout//60} phút. Task vẫn đang xử lý: {task_id}")
            
            try:
                status = self.get_task_status(task_id)
                current_status = status.get("status") or status.get("data", {}).get("status", "UNKNOWN")
                
                # Chỉ in trạng thái khi có thay đổi
                if current_status != last_status:
                    last_status = current_status
                    print(f"✅ [{elapsed:4}s] Trạng thái mới: {current_status}")
                
                if current_status in {"succeeded", "SUCCESS"}:
                    content = status.get("content") or status.get("data", {}).get("content") or {}
                    video_url = content.get("video_url")
                    if video_url:
                        print(f"\n🎉 HOÀN THÀNH sau {elapsed} giây!")
                        print(f"🔗 URL video: {video_url}")
                        return video_url

                    outputs = status.get("output") or status.get("data", {}).get("output") or []
                    if outputs and isinstance(outputs, list) and isinstance(outputs[0], dict) and "url" in outputs[0]:
                        video_url = outputs[0]["url"]
                        print(f"\n🎉 HOÀN THÀNH sau {elapsed} giây!")
                        print(f"🔗 URL video: {video_url}")
                        return video_url
                    return None
                
                if current_status in {"failed", "FAILED", "error"}:
                    error_obj = status.get("error") or status.get("data", {}).get("error") or {}
                    msg = error_obj.get("message") or status.get("error_message") or status.get("data", {}).get("error_message") or "Lỗi không xác định"
                    error_code = error_obj.get("code", "") or status.get("error_code", "") or status.get("data", {}).get("error_code", "")
                    raise Exception(f"❌ Tạo video thất bại: [{error_code}] {msg}")

                if current_status in {"cancelled", "expired"}:
                    raise RuntimeError(f"Task kết thúc với trạng thái: {current_status}")
                
                # Reset retry count khi kết nối thành công
                retry_count = 0
                
            except requests.exceptions.RequestException as e:
                retry_count += 1
                wait_backoff = min(2 ** retry_count, 30)
                print(f"⚠️  Lỗi kết nối (lần {retry_count}): {str(e)}. Thử lại sau {wait_backoff}s...")
                time.sleep(wait_backoff)
                continue
            
            except Exception as e:
                print(f"⚠️  Lỗi không xác định: {str(e)}. Tiếp tục theo dõi...")
            
            # Đợi trước khi kiểm tra lại
            time.sleep(poll_interval)

    def generate_long_video(
        self,
        prompt: str,
        ratio: str = "16:9",
        resolution: str = "720p",
        total_duration: int = 30,
        generate_audio: bool = True,
        image_urls: Optional[List[str]] = None,
        segment_duration: int = 15,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        ✅ Tạo video dài hơn 15s bằng cách tự động chia thành nhiều segment
        Tự động truyền last frame của segment trước làm ảnh đầu vào segment kế tiếp để đảm bảo tính liên tục
        
        Args:
            total_duration: Tổng thời lượng video mong muốn (có thể >15s)
            segment_duration: Độ dài mỗi segment (mặc định 15s - giới hạn Seedance)
            Các tham số khác giống generate_video()
            
        Returns:
            Danh sách kết quả từng segment, bao gồm video url và last frame url
        """
        import math
        import time
        
        num_segments = math.ceil(total_duration / segment_duration)
        print(f"📋 Tổng thời lượng {total_duration}s → chia thành {num_segments} segment mỗi đoạn {segment_duration}s")
        
        segments_result = []
        previous_last_frame = None
        
        for seg_idx in range(num_segments):
            print(f"\n⏳ Đang xử lý segment {seg_idx+1}/{num_segments}")
            
            # Chuẩn bị ảnh đầu vào: nếu có segment trước thì thêm last frame làm ảnh đầu
            current_images = image_urls.copy() if image_urls else []
            if previous_last_frame is not None:
                print(f"🔗 Sử dụng last frame của segment trước làm ảnh tham chiếu đầu")
                current_images.insert(0, previous_last_frame)
            
            # Gọi API tạo segment này
            task_resp = self.generate_video(
                prompt=prompt,
                ratio=ratio,
                resolution=resolution,
                duration=segment_duration,
                generate_audio=generate_audio,
                image_urls=current_images,
                return_last_frame=True,
                **kwargs
            )
            task_id = task_resp["id"]
            
            # Đợi segment hoàn thành
            video_url = self.wait_for_video(task_id)
            
            # Lấy last frame từ task kết quả
            task_status = self.get_task_status(task_id)
            content = task_status.get("content") or task_status.get("data", {}).get("content") or {}
            last_frame_url = content.get("last_frame_url")
            
            segments_result.append({
                "segment_index": seg_idx,
                "task_id": task_id,
                "video_url": video_url,
                "last_frame_url": last_frame_url
            })
            
            # Lưu last frame cho segment kế tiếp
            previous_last_frame = last_frame_url
            print(f"✅ Segment {seg_idx+1} hoàn thành. Last frame đã được lưu cho đoạn tiếp theo")
            
        print(f"\n🎉 Tất cả {num_segments} segment đã được tạo thành công!")
        return segments_result

    def merge_video_segments(self, segments: List[Dict[str, Any]], output_file: str = "final_video.mp4") -> str:
        """
        ✅ Ghép tất cả các segment video thành 1 file hoàn chỉnh bằng ffmpeg
        Sử dụng concat lossless không re-encode để giữ nguyên chất lượng
        
        Args:
            segments: Kết quả trả về từ generate_long_video()
            output_file: Đường dẫn file output cuối cùng
            
        Returns:
            Đường dẫn file video đã ghép xong
        """
        import os
        import tempfile
        import subprocess
        
        print(f"\n🔀 Bắt đầu ghép {len(segments)} segment video...")
        
        # Tạo file danh sách cho ffmpeg concat
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            for seg in segments:
                video_url = seg["video_url"]
                f.write(f"file '{video_url}'\n")
            list_file = f.name
        
        try:
            # Chạy ffmpeg concat không re-encode (nhanh nhất, giữ nguyên chất lượng)
            cmd = [
                "ffmpeg",
                "-f", "concat",
                "-safe", "0",
                "-i", list_file,
                "-c", "copy",
                "-y",
                output_file
            ]
            
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True
            )
            
            file_size = os.path.getsize(output_file) / (1024 * 1024)
            print(f"✅ Ghép video thành công! File cuối: {output_file} ({file_size:.1f} MB)")
            return output_file
            
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Lỗi khi ghép video ffmpeg: {e.stderr}")
        finally:
            os.unlink(list_file)
    
    def list_tasks(
        self,
        page_num: int = 1,
        page_size: int = 20,
        filter_status: Optional[str] = None,
        filter_task_ids: Optional[List[str]] = None,
        filter_model: Optional[str] = None,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {
            "page_num": page_num,
            "page_size": page_size,
        }
        if filter_status:
            params["filter.status"] = filter_status
        if filter_task_ids:
            params["filter.task_ids"] = ",".join(filter_task_ids)
        if filter_model:
            params["filter.model"] = filter_model

        response = requests.get(
            f"{self.base_url}/tasks",
            headers=self.headers,
            params=params,
            timeout=self.timeout_s,
        )
        self._raise_for_api_error(response)
        return response.json()

    def cancel_or_delete_task(self, task_id: str) -> None:
        response = requests.delete(
            f"{self.base_url}/tasks/{task_id}",
            headers=self.headers,
            timeout=self.timeout_s,
        )
        self._raise_for_api_error(response)
