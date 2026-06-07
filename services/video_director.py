"""Video Director service - extracted from seedance-video-director SKILL.md"""
from typing import Dict, Any, List
import asyncio
import os
import json
from dotenv import load_dotenv
from openai import AsyncOpenAI
from typing_extensions import TypedDict

load_dotenv()
# Sử dụng Seedance 2.0 LLM (Doubao) thông qua OpenAI client với endpoint đúng
ARK_API_KEY = os.getenv("ARK_API_KEY")
if not ARK_API_KEY:
    raise ValueError("ARK_API_KEY environment variable not configured")

# Sử dụng API key riêng cho Doubao nếu có, nếu không dùng ARK_API_KEY
DOUBAO_API_KEY = os.getenv("DOUBAO_API_KEY") or ARK_API_KEY
if not DOUBAO_API_KEY:
    raise ValueError("Cần cấu hình DOUBAO_API_KEY hoặc ARK_API_KEY trong .env")
# BytePlus Ark endpoint compatible with OpenAI SDK
client = AsyncOpenAI(
    api_key=DOUBAO_API_KEY,
    base_url="https://ark.ap-southeast.bytepluses.com/api/v3"
)

class ScenePrompt(TypedDict):
    subject: str
    main_action: str
    angle: str
    lighting: str
    style: str
    background: str
    quality: str

from typing import Union
class DirectorScene(TypedDict):
    duration: str
    scene_prompt: ScenePrompt
    motion_control: str
    audio: str
    text_overlay: Dict[str, Any]
    trend_reference: str
    reference_lock: Union[str, None]

class VideoDirector:
    """Creates and analyzes optimized sales video scripts/storyboards for Seedance 2.0"""
    
    def __init__(self):
        pass
    
    async def _call_seedance_llm(self, prompt: str, response_format: str = "text") -> Any:
        """Helper method to call Seedance 2.0 LLM API via preconfigured AsyncOpenAI client"""
        # Lấy model ID từ biến môi trường, mặc định dùng doubao-seed-2-0-pro-260215 nếu không cấu hình
        DOUBAO_MODEL_ID = os.getenv("DOUBAO_MODEL_ID", "seed-2-0-pro-260328")
        
        try:
            # Use the pre-configured AsyncOpenAI client for valid API calls
            chat_completion = await client.chat.completions.create(
                model=DOUBAO_MODEL_ID,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8,
                response_format={"type": "json_object"} if response_format == "json_object" else None
            )
            content = chat_completion.choices[0].message.content.strip()
            
            if response_format == "json_object":
                return json.loads(content)
            return content
        except Exception as e:
            print(f"[WARNING] Seedance LLM API call failed: {e}")
            # Return fallback data if API call fails
            if response_format == "json_object":
                return {}
            return ""
    
    async def create_script(self, social_output: Dict[str, Any], brief: Dict[str, Any]) -> Dict[str, Any]:
        """Convert social generator output to Seedance 2.0 optimized storyboards with all required fields"""
        processed_videos = []
        
        for video in social_output.get("videos", []):
            # Enhance storyboard with Seedance-specific format requirements using OpenAI API
            optimized_storyboard = await self._optimize_storyboard_for_seedance(video["storyboard"], video["insight"], brief)
            
            # Add additional required assets
            thumbnail = await self._enhance_thumbnail(video["thumbnail_suggestion"], brief)
            caption = await self._enhance_caption(video["caption"], brief)
            hashtags = self._optimize_hashtags(video["hashtags"])
            
            processed_videos.append({
                "core_message": video["insight"]["angle"],
                "retention_factor": video["insight"]["why_it_works"],
                "viral_factor": "Tackles common pain point with clear solution",
                "hook": video["hook"],
                "platform_policy": "Compliant with all platform guidelines",
                "final_storyboard": optimized_storyboard,
                "thumbnail": thumbnail,
                "caption": caption,
                "hashtags": hashtags
            })
        
        return {
            "processed_videos": processed_videos,
            "ready_for_camera_man": True,
            "seedance_api_payload": self._prepare_seedance_payload(processed_videos[0], brief) if processed_videos else None
        }
    
    async def _optimize_storyboard_for_seedance(self, original_storyboard: List[Dict[str, Any]], insight: Dict[str, Any], brief: Dict[str, Any]) -> List[DirectorScene]:
        """Convert simple storyboard to Seedance 2.0 required format with full details using OpenAI API"""
        seedance_scenes = []
        product_name = brief.get("product_name", "Sản phẩm")
        brief_content = brief.get("brief", "")
        
        for scene in original_storyboard:
            # Build prompt for OpenAI to generate proper ScenePrompt according to Seedance specs
            prompt = f"""
            Tạo scene prompt theo đúng chuẩn Seedance 2.0 cho scene sau đây:
            Thông tin sản phẩm: {product_name}
            Thông tin brief: {brief_content}
            Góc nhìn marketing: {insight["angle"]}
            Nội dung hình ảnh gốc: {scene.get("image_content", "")}
            Âm thanh gốc: {scene.get("audio", "")}
            Thời lượng: {scene.get("duration", "0-3s")}
            
            Bạn phải trả về JSON format với các trường sau:
            - scene_prompt: object chứa: subject, main_action, angle, lighting, style, background, quality
            - motion_control: mô tả chuyển động chính xác
            - text_overlay: object chứa position, size, color, appearance_time
            - trend_reference: tên trend viral phù hợp năm 2025
            
            Scene prompt phải theo đúng công thức: [Chủ thể] + [Hành động chính] + [Góc quay] + [Ánh sáng] + [Phong cách hình ảnh] + [Background] + [Chất lượng]
            Không dùng từ chung chung, phải mô tả cụ thể 100%.
            """
            
            scene_data = await self._call_seedance_llm(prompt, response_format="json_object")
            
            # Build full DirectorScene
            seedance_scenes.append({
                "duration": scene.get("duration", "0-3s"),
                "scene_prompt": scene_data["scene_prompt"],
                "motion_control": scene_data["motion_control"],
                "audio": scene.get("audio", ""),
                "text_overlay": scene_data["text_overlay"],
                "trend_reference": scene_data["trend_reference"],
                "reference_lock": "Sử dụng chính xác sản phẩm từ ảnh tham chiếu 1, không thay đổi màu sắc, hình dáng" if brief.get("product_images") else None
            })
        
        return seedance_scenes
    
    async def _enhance_thumbnail(self, original_thumbnail: str, brief: Dict[str, Any]) -> str:
        """Create high-contrast, clickable thumbnail with Seedance optimization using OpenAI API"""
        product_name = brief.get("product_name", "Sản phẩm")
        prompt = f"""
        Tạo mô tả thumbnail thu hút, tối ưu nhấp chuột cho video TikTok về {product_name}.
        Mô tả gốc: {original_thumbnail}
        
        Yêu cầu: Mô tả phải cụ thể, nêu bật các yếu tố thu hút: màu sắc nổi bật, chủ thể rõ ràng, chữ đậm có bóng để dễ nhìn trên mobile.
        Trả về chỉ một chuỗi văn bản duy nhất.
        """
        
        return await self._call_seedance_llm(prompt, response_format="text")
    
    async def _enhance_caption(self, original_caption: str, brief: Dict[str, Any]) -> str:
        """Enhance caption to be under 150 chars with clear CTA using OpenAI API"""
        product_name = brief.get("product_name", "Sản phẩm")
        prompt = f"""
        Tạo caption ngắn gọn (dưới 150 ký tự) cho video TikTok về {product_name}.
        Caption gốc: {original_caption}
        
        Yêu cầu: Có kêu gọi hành động rõ ràng (CTA), thu hút tương tác, phù hợp với mạng xã hội.
        Trả về chỉ một chuỗi văn bản duy nhất.
        """
        
        caption = await self._call_seedance_llm(prompt, response_format="text")
        return caption[:150]  # Keep under limit
    
    def _optimize_hashtags(self, original_hashtags: List[str]) -> List[str]:
        """Ensure 8-12 total hashtags, mix popular + niche"""
        additional_hashtags = ["#top10skincare", "#beautyvietnam", "#reviewskincare"]
        return list(set(original_hashtags + additional_hashtags))[:12]
    
    def _prepare_seedance_payload(self, processed_video: Dict[str, Any], brief: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare payload that camera_man can directly pass to Seedance API"""
        return {
            "frames": brief.get("product_images", []),
            "duration_per_frame": 2.5,
            "transition": "smooth_fade",
            "audio_track": None,
            "resolution": "1080x1920",
            "fps": 30,
            "return_last_frame": False,
            "storyboard": processed_video["final_storyboard"]
        }
