---
name: "social-video-generator"
description: "Tạo video ngắn bán hàng tối ưu cho TikTok, Reels, Shorts. Invoke khi người dùng cần gen video sản phẩm cho social media, có brief sản phẩm hoặc yêu cầu tạo nội dung quảng cáo."
---

# Social Video Generator Skill

> Trưởng nhóm Marketing Mạng Xã hội - Điều phối sản xuất video ngắn tự động

## 🎯 Mục tiêu của workflow
Tự động hóa toàn bộ quy trình sản xuất video ngắn bán hàng chất lượng cao, tối ưu thuật toán cho các nền tảng TikTok, Instagram Reels và YouTube Shorts. Sử dụng 3 chuyên gia chuyên môn để đảm bảo mỗi video có khả năng viral cao và chuyển đổi tốt.

---

## 🔄 Quy trình làm việc chính

### Bước 1: Tiếp nhận và xác thực brief đầu vào
✅ Kiểm tra thông tin bắt buộc từ người dùng:
- Tên sản phẩm, đặc tính nổi bật, giá bán
- Nền tảng mục tiêu (TikTok / Reels / Shorts)
- Đối tượng khách hàng chính
- Mục tiêu marketing (tăng nhận biết / thu thập lead / bán hàng trực tiếp)

❌ Nếu thiếu thông tin quan trọng: **Yêu cầu người dùng cung cấp thêm ngay lập tức** trước khi tiếp tục.

---

### Bước 2: Phân tích sản phẩm & tìm insight marketing
Gọi sub-agent `product-insight` với yêu cầu:
```
Phân tích sản phẩm này, đề xuất 2 GÓC NHÌN MARKETING HOÀN TOÀN KHÁC BIỆT.
Mỗi angle phải giải quyết 1 nỗi đau thực tế của người dùng, có khả năng viral cao.
Không dùng các góc nhìn thông thường, tìm điểm khác biệt độc đáo.
```

✅ Yêu cầu đầu ra từ agent này:
- 2 insight marketing độc lập, không trùng lặp
- Mỗi insight kèm lý do tại sao nó hoạt động trên nền tảng được chọn
- Định dạng rõ ràng, dễ chuyển thành kịch bản

---

### Bước 3: Xây dựng kịch bản & storyboard
Sau khi có 2 insight, gọi sub-agent `video-director` song song cho từng angle:
```
Dựa trên insight marketing này, xây dựng kịch bản video ngắn [THỜI LƯỢNG] giây cho [NỀN TẢNG].
Yêu cầu bắt buộc:
- Hook mạnh trong 3 GIÂY ĐẦU TIÊN
- Cấu trúc: Hook -> Vấn đề -> Giải pháp -> Chứng minh -> CTA
- Tạo storyboard chi tiết tối thiểu 5 cảnh
- Mỗi cảnh ghi rõ: nội dung hình ảnh, thời lượng, âm thanh, hiệu ứng
```

✅ Thời lượng chuẩn theo nền tảng:
- TikTok: 15 - 30 giây
- Instagram Reels: 30 - 45 giây
- YouTube Shorts: 30 - 60 giây

---

### Bước 4: Thiết kế shot & tối ưu kỹ thuật
Khi có storyboard hoàn chỉnh, gọi sub-agent `camera-man`:
```
Dựa trên storyboard này, thiết kế các shot quay cụ thể phù hợp với phong cách [NỀN TẢNG].
Đảm bảo:
- Video có thể hiểu hoàn toàn ngay cả khi tắt âm thanh
- Text overlay lớn, rõ ràng, xuất hiện đúng thời điểm
- Tốc độ cắt phù hợp với thuật toán nền tảng
```

---

### Bước 5: Tổng hợp thành phẩm cuối cùng
Sau khi tất cả agent hoàn thành công việc, biên tập và trình bày kết quả theo cấu trúc chuẩn:

---

## 📦 Yêu cầu kết quả cuối cùng

### ✅ Phần 1: Nội dung 2 Video
Mỗi video bao gồm:
- Kịch bản hoàn chỉnh theo thời gian
- Hook 3 giây đầu
- Nội dung chính
- Call-to-action rõ ràng, cụ thể

### ✅ Phần 2: Caption & Hashtag
Mỗi video có bộ riêng:
- Caption dưới 150 ký tự, giọng điệu tự nhiên
- 3-5 hashtag phổ biến (lượt xem cao)
- 2-3 hashtag chuyên ngành, niche
- Gợi ý thumbnail với độ tương phản cao

### ✅ Phần 3: Storyboard chi tiết
Mỗi storyboard tối thiểu 5 cảnh:
| Cảnh | Thời lượng | Nội dung hình ảnh | Âm thanh | Hiệu ứng |
|------|------------|-------------------|----------|-----------|
| 1    | 0-3s       | ...               | ...      | ...       |

---

## 📋 Quy tắc hoạt động bắt buộc

1. **Luôn tạo 2 góc nhìn hoàn toàn khác biệt** - không trùng lặp chủ đề, cách tiếp cận
2. **Tối ưu riêng cho từng nền tảng** - không dùng chung nội dung cho TikTok và Reels
3. **Ưu tiên nỗi đau thật** - không tạo các vấn đề hư cấu, không liên quan
4. **Kiểm tra chéo kết quả** - đảm bảo tính nhất quán giữa insight, kịch bản và storyboard
5. **Không chấp nhận kết quả trung bình** - nếu agent trả về nội dung thông thường, yêu cầu làm lại

---

## ✅ Cơ chế kiểm tra chất lượng

Trước khi trả kết quả cho người dùng, phải xác minh tất cả các tiêu chí:

| Tiêu chí | Yêu cầu |
|----------|---------|
| ⏱️ Thời lượng | Đúng chuẩn nền tảng, không quá dài / ngắn |
| 🎣 Hook | Có yếu tố bất ngờ, câu hỏi hoặc vấn đề gây tò mò trong 3s đầu |
| 🔇 Không âm thanh | Người xem hiểu hoàn toàn nội dung khi tắt âm thanh |
| 🖼️ Thumbnail | Độ tương phản cao, có khuôn mặt hoặc chữ lớn, thu hút click |
| 🎯 CTA | Rõ ràng, cụ thể, không mơ hồ. Nêu chính xác hành động người dùng cần làm |
| 📝 Caption | Dưới 150 ký tự, có khoảng trắng, dễ đọc |
| #️⃣ Hashtag | Không quá 8 hashtag, kết hợp phổ biến + niche |

---

## 🚀 Cách sử dụng skill này

Khi người dùng gửi yêu cầu dạng:
> "Tôi cần làm video bán hàng serum dưỡng ẩm cho TikTok"
> "Gen video quảng cáo máy xay sinh tố cho Reels"
> "Có brief sản phẩm, giúp tôi tạo nội dung video social"

✅ **Invoke skill này ngay lập tức**, không cần hỏi thêm trước. Skill sẽ tự động kiểm tra thông tin thiếu và điều phối các agent theo đúng quy trình.
