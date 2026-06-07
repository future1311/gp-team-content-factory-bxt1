"""Social Video Generator service - extracted from social-video-generator SKILL.md"""
from typing import Dict, Any, List
import asyncio
import os
import json
from dotenv import load_dotenv
from openai import AsyncOpenAI
from typing_extensions import TypedDict

load_dotenv()
# social-video-generator LUÔN dùng OpenAI GPT-4o với OPENAI_API_KEY
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("Cần cấu hình OPENAI_API_KEY trong .env cho social-video-generator")
client = AsyncOpenAI(api_key=OPENAI_API_KEY)

class StoryboardScene(TypedDict):
    scene: int
    duration: str
    image_content: str
    audio: str
    effects: str

class VideoOutput(TypedDict):
    script: str
    hook: str
    main_content: str
    cta: str
    caption: str
    hashtags: List[str]
    thumbnail_suggestion: str
    storyboard: List[StoryboardScene]

class SocialVideoGenerator:
    """Generates optimized short video content for TikTok/Reels/Shorts from user's brief"""
    
    def __init__(self):
        pass
    
    async def generate(self, brief: Dict[str, Any]) -> Dict[str, Any]:
        """Generate social video content following the workflow from SKILL.md"""
        # Step 1: Proceed to analyze product
        insights = await self._extract_marketing_insights(brief)
        
        # Step 2: Generate 2 different marketing angles
        video_outputs = []
        for insight in insights:
            # Build script and storyboard
            script = await self._build_script(insight, brief)
            storyboard = await self._create_storyboard(insight, brief)
            
            # Generate caption and hashtags
            caption, hashtags = await self._generate_caption_hashtags(insight, brief)
            thumbnail = await self._generate_thumbnail_suggestion(insight, brief)
            
            video_outputs.append({
                "insight": insight,
                "script": script,
                "hook": storyboard[0]["audio"] if storyboard else "",
                "main_content": script,
                "cta": "Mua ngay để trải nghiệm!",
                "caption": caption,
                "hashtags": hashtags,
                "thumbnail_suggestion": thumbnail,
                "storyboard": storyboard
            })
        
        return {
            "videos": video_outputs,
            "platform": brief.get("ratio", "9:16"),
            "duration": brief.get("duration", 15)
        }
    
    async def _extract_marketing_insights(self, brief: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract 2 unique marketing insights from product brief - Gọi LLM API thật theo yêu cầu SKILL.md"""
        brief_content = brief.get("brief", "")
        product_name = brief.get("product_name", "Sản phẩm")
        
        # Gọi API OpenAI đúng theo prompt trong SKILL.md - Sử dụng cú pháp mới openai >=1.0.0
        prompt = f"""
        Phân tích sản phẩm này, đề xuất 2 GÓC NHÌN MARKETING HOÀN TOÀN KHÁC BIỆT.
        Mỗi angle phải giải quyết 1 nỗi đau thực tế của người dùng, có khả năng viral cao.
        Không dùng các góc nhìn thông thường, tìm điểm khác biệt độc đáo.
        
        Tên sản phẩm: {product_name}
        Brief sản phẩm: {brief_content}
        
        Trả về JSON format: [{{"angle": "...", "why_it_works": "..."}}, ...]
        """
        
        # social-video-generator LUÔN dùng OpenAI GPT-4o
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
            response_format={"type": "json_object"}
        )
        
        try:
            insights = json.loads(response.choices[0].message.content)
            # Ensure we always return a list, even if JSON parsing returned something else
            if not isinstance(insights, list):
                if isinstance(insights, dict) and "insights" in insights:
                    insights = insights["insights"]
                else:
                    # Fallback to default insights if parsing failed
                    insights = [
                        {"angle": "Giải pháp tiện ích cho cuộc sống hiện đại", "why_it_works": "Đáp ứng nhu cầu cấp thiết của người dùng"},
                        {"angle": "Chất lượng vượt trội với giá thành hợp lý", "why_it_works": "Tạo sự khác biệt so với các sản phẩm cùng phân khúc"}
                    ]
        except Exception as e:
            print(f"[WARNING] Failed to parse OpenAI insights JSON: {e}")
            # Return default insights if JSON parsing fails
            insights = [
                {"angle": "Giải pháp tiện ích cho cuộc sống hiện đại", "why_it_works": "Đáp ứng nhu cầu cấp thiết của người dùng"},
                {"angle": "Chất lượng vượt trội với giá thành hợp lý", "why_it_works": "Tạo sự khác biệt so với các sản phẩm cùng phân khúc"}
            ]
        return insights
    
    async def _build_script(self, insight: Dict[str, Any], brief: Dict[str, Any]) -> str:
        """Build full video script following Hook -> Problem -> Solution -> Proof -> CTA structure"""
        product_name = brief.get("product_name", "Sản phẩm")
        brief_content = brief.get("brief", "")
        
        prompt = f"""
        Tạo kịch bản video ngắn 15 giây theo cấu trúc: Hook -> Problem -> Solution -> Proof -> CTA
        Thông tin sản phẩm: {product_name}
        Brief: {brief_content}
        Góc nhìn marketing: {insight['angle']}
        Lý do hiệu quả: {insight['why_it_works']}
        
        Trả về một chuỗi văn bản duy nhất với kịch bản hoàn chỉnh, phù hợp với giọng văn tự nhiên trên TikTok.
        """
        
        # social-video-generator LUÔN dùng OpenAI GPT-4o
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8
        )
        
        return response.choices[0].message.content.strip()
    
    async def _create_storyboard(self, insight: Dict[str, Any], brief: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create detailed storyboard with minimum 5 scenes using OpenAI API"""
        duration = brief.get("duration", 15)
        product_name = brief.get("product_name", "Sản phẩm")
        brief_content = brief.get("brief", "")
        
        prompt = f"""
        Tạo storyboard chi tiết cho video ngắn {duration} giây về {product_name}.
        Brief: {brief_content}
        Góc nhìn marketing: {insight['angle']}
        
        Tạo ít nhất 5 scene, mỗi scene có:
        - scene: số thứ tự
        - duration: khoảng thời gian (ví dụ "0-3s")
        - image_content: mô tả hình ảnh chi tiết
        - audio: nội dung âm thanh/voiceover
        - effects: hiệu ứng hình ảnh
        
        Trả về JSON format với key là "scenes" chứa mảng các scene.
        """
        
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        data = json.loads(response.choices[0].message.content)
        return data.get("scenes", [])
    
    async def _generate_caption_hashtags(self, insight: Dict[str, Any], brief: Dict[str, Any]) -> tuple[str, List[str]]:
        """Generate social media caption and hashtags using OpenAI API"""
        product_name = brief.get("product_name", "Sản phẩm")
        platform = brief.get("ratio", "9:16")
        
        prompt = f"""
        Tạo caption và hashtag cho video TikTok về {product_name}.
        Góc nhìn marketing: {insight['angle']}
        
        Yêu cầu:
        - Caption ngắn gọn dưới 150 ký tự, có CTA rõ ràng
        - Tạo 8-12 hashtag kết hợp phổ biến và niche (ngành hàng cụ thể)
        - Trả về JSON format: {{"caption": "...", "hashtags": ["#...", ...]}}
        """
        
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        data = json.loads(response.choices[0].message.content)
        return data.get("caption", "")[:150], data.get("hashtags", [])
    
    async def _generate_thumbnail_suggestion(self, insight: Dict[str, Any], brief: Dict[str, Any]) -> str:
        """Generate high-contrast thumbnail that attracts clicks using OpenAI API"""
        product_name = brief.get("product_name", "Sản phẩm")
        
        prompt = f"""
        Tạo mô tả thumbnail thu hút nhấp chuột cho video TikTok về {product_name}.
        Góc nhìn marketing: {insight['angle']}
        
        Yêu cầu: Mô tả chi tiết về màu sắc, chủ thể, text overlay, đảm bảo nổi bật trên feed mobile.
        Trả về chỉ một chuỗi văn bản duy nhất.
        """
        
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
