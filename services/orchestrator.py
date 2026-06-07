"""Agent Orchestrator service - extracted from agent-orchestor SKILL.md"""
from typing import Dict, Any, Optional, List
import asyncio
import json
from .social_video_generator import SocialVideoGenerator
from .video_director import VideoDirector
from .camera_man import SeedanceCameraMan

# Global reference to main's tasks_db - set via update_task_db_reference()
_global_tasks_db: Dict[str, Dict[str, Any]] = {}

def update_task_db_reference(tasks_db: Dict[str, Dict[str, Any]]) -> None:
    """Update reference to main's global tasks_db to avoid circular import"""
    global _global_tasks_db
    _global_tasks_db.clear()
    _global_tasks_db.update(tasks_db)

class AgentOrchestrator:
    """Orchestrates video creation workflow sequentially:
    social-video-generator → seedance-video-director → seedance2-camera-man
    with direct execution when brief is available.
    """
    
    def __init__(self):
        self.social_generator = SocialVideoGenerator()
        self.video_director = VideoDirector()
        self.camera_man = SeedanceCameraMan()
    
    async def process_video(self, brief: Dict[str, Any], task_id: str) -> Dict[str, Any]:
        """Process full video creation workflow"""
        print(f"[DEBUG] Task {task_id}: Bắt đầu xử lý - KIỂM TRA THÔNG TIN ĐẦU VÀO")

        # Step 1: Execute skills in sequence with frontend status updates
        import time
        start_time = time.time()
        print(f"[DEBUG] Task {task_id}: === BẮT ĐẦU XỬ LÝ TẤT CẢ CÁC STEP - {start_time:.0f}")
        # Ép kiểu duration thành số nguyên chắc chắn để tránh lỗi so sánh
        brief["duration"] = int(brief.get("duration", 15))
        try:
            # 1. Run social-video-generator
            print(f"[DEBUG] Task {task_id}: [+{time.time()-start_time:.0f}s] === BƯỚC 1: GỌI SOCIAL-VIDEO-GENERATOR ===")
            self._update_task_status(task_id, "social_video_generator", "Đang tạo nội dung video tối ưu...", None)
            print(f"[DEBUG] Task {task_id}: [+{time.time()-start_time:.0f}s] Đã cập nhật trạng thái social_video_generator")
            await asyncio.sleep(3)  # Chờ 3s để frontend kịp nhận trạng thái
            print(f"[DEBUG] Task {task_id}: [+{time.time()-start_time:.0f}s] Bắt đầu chạy social_generator.generate()...")
            social_output = await self.social_generator.generate(brief)
            print(f"[DEBUG] Task {task_id}: [+{time.time()-start_time:.0f}s] social_generator.generate() HOÀN THÀNH - full output: {json.dumps(social_output, indent=2, ensure_ascii=False)}")

            self._update_task_status(task_id, "social_video_generator_completed", "Hoàn thành tạo nội dung...", social_output)
            print(f"[DEBUG] Task {task_id}: [+{time.time()-start_time:.0f}s] Đã cập nhật trạng thái social_video_generator_completed")
            await asyncio.sleep(3)  # Chờ 3s cho frontend cập nhật
            
            # 2. Run seedance-video-director
            print(f"[DEBUG] Task {task_id}: [+{time.time()-start_time:.0f}s] === BƯỚC 2: GỌI SEEDANCE-VIDEO-DIRECTOR ===")
            self._update_task_status(task_id, "seedance_video_director", "Đang xây dựng storyboard & kịch bản...", None)
            print(f"[DEBUG] Task {task_id}: [+{time.time()-start_time:.0f}s] Đã cập nhật trạng thái seedance_video_director")
            await asyncio.sleep(3)
            print(f"[DEBUG] Task {task_id}: [+{time.time()-start_time:.0f}s] Bắt đầu chạy video_director.create_script()...")
            director_output = await self.video_director.create_script(social_output, brief)
            print(f"[DEBUG] Task {task_id}: [+{time.time()-start_time:.0f}s] video_director.create_script() HOÀN THÀNH - full output: {json.dumps(director_output, indent=2, ensure_ascii=False)}")
            self._update_task_status(task_id, "seedance_video_director_completed", "Hoàn thành xây dựng kịch bản...", director_output)
            print(f"[DEBUG] Task {task_id}: [+{time.time()-start_time:.0f}s] Đã cập nhật trạng thái seedance_video_director_completed")
            await asyncio.sleep(3)
            
            # 3. Run seedance2-camera-man to generate final video
            print(f"[DEBUG] Task {task_id}: [+{time.time()-start_time:.0f}s] === BƯỚC 3: GỌI SEEDANCE2-CAMERA-MAN ===")
            self._update_task_status(task_id, "seedance2_camera_man", "Đang tạo video cuối cùng...", None)
            print(f"[DEBUG] Task {task_id}: [+{time.time()-start_time:.0f}s] Đã cập nhật trạng thái seedance2_camera_man")
            await asyncio.sleep(3)
            print(f"[DEBUG] Task {task_id}: [+{time.time()-start_time:.0f}s] Bắt đầu chạy camera_man.generate_video()...")
            final_video = await self.camera_man.generate_video(director_output, brief)
            print(f"[DEBUG] Task {task_id}: [+{time.time()-start_time:.0f}s] camera_man.generate_video() HOÀN THÀNH - full output: {json.dumps(final_video, indent=2, ensure_ascii=False)}")
            self._update_task_status(task_id, "seedance2_camera_man_completed", "Hoàn thành tạo video cuối cùng...", final_video)
            await asyncio.sleep(3)
            
            return {
                "status": "completed",
                "current_step": "finished",
                "message": "Quy trình tạo video đã hoàn thành!",
                "video_url": final_video.get("video_url"),
                "social_output": social_output,
                "director_output": director_output
            }
            
        except Exception as e:
            print(f"[ERROR] Task {task_id}: {str(e)}")
            self._update_task_status(task_id, "processing_failed", f"Lỗi trong quá trình xử lý: {str(e)}", {"error": str(e)})
            return {
                "status": "failed",
                "error": str(e),
                "message": f"Lỗi trong quá trình xử lý: {str(e)}"
            }
    
    def _update_task_status(self, task_id: str, current_step: str, message: str, step_output: Any = None) -> None:
        """Update task status and save step output in global tasks_db to notify frontend"""
        if task_id in _global_tasks_db:
            update_data: Dict[str, Any] = {
                "current_step": current_step,
                "message": message
            }
            # Save output of the step if provided
            if step_output is not None:
                output_key = f"{current_step}_output"
                update_data[output_key] = step_output
                # Also save to step_outputs history for full tracking
                if "step_outputs" not in _global_tasks_db[task_id]:
                    _global_tasks_db[task_id]["step_outputs"] = {}
                _global_tasks_db[task_id]["step_outputs"][current_step] = step_output
            
            _global_tasks_db[task_id].update(update_data)
            print(f"[DEBUG] Task {task_id}: {message} (output saved: {step_output is not None})")
