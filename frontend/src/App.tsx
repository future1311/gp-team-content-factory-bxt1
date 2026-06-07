import { useState, useEffect, useRef } from 'react';
import './App.css';

interface Message {
  id: string;
  role: 'user' | 'bot';
  content: string;
  images?: string[];
}

interface VideoBrief {
  brief: string;
  product_images?: string[];
  ratio: string;
  duration: number;
  generate_audio: boolean;
}

interface TaskStatus {
  task_id: string;
  status: string;
  current_step: string;
  video_url?: string;
  error?: string;
  confirmation_required?: {
    field: string;
    message: string;
    current_value?: any;
  }[];
}

// Generate unique ID for messages to avoid duplicates
let messageCounter = 0;
const generateUniqueId = () => {
  messageCounter += 1;
  return `${Date.now()}-${messageCounter}`;
};

function App() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'bot',
      content: '👋 Xin chào! Tôi là Seedance AI Assistant. Tôi sẽ giúp bạn tạo video marketing cho sản phẩm.\n\n📋 Bạn cần cung cấp các thông tin sau:\n• Tên sản phẩm & đặc tính nổi bật\n• Giá bán\n• Nền tảng: TikTok / Reels / Shorts\n• Đối tượng khách hàng\n• Mục tiêu marketing\n\n📷 Bạn có thể upload ảnh sản phẩm bằng nút 📷\n✅ Video sẽ tự động được tạo sau khi bạn cung cấp đủ thông tin\n\n💡 Ví dụ brief đầy đủ:\nÁo thun print on demand, chất liệu cotton cao cấp, không bị xù lông, giá 350k, đăng TikTok, đối tượng giới trẻ 16-28, mục tiêu bán hàng trực tiếp - chạm vào cảm xúc thể hiện cá tính'
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [uploadedImages, setUploadedImages] = useState<string[]>([]);
  const [currentTask, setCurrentTask] = useState<TaskStatus | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [lastReportedStep, setLastReportedStep] = useState<string>(''); // Lưu bước đã báo cáo để không duplicate
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const API_BASE = 'http://localhost:8000';

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    const isTerminalStatus = currentTask
      ? ['completed', 'failed'].includes(currentTask.status)
      : false;

    // Poll ngay lập tức để cập nhật trạng thái, mỗi 3s gọi lại 1 lần
    if (currentTask && !isTerminalStatus) {
      fetchTask(currentTask.task_id);
      const interval = setInterval(() => {
        fetchTask(currentTask.task_id);
      }, 3000);
      return () => clearInterval(interval);
    }
  }, [currentTask?.task_id, currentTask?.status]);

  const addBotMessage = (content: string) => {
    setMessages(prev => [...prev, {
      id: generateUniqueId(),
      role: 'bot',
      content
    }]);
  };

  const addUserMessage = (content: string, images?: string[]) => {
    setMessages(prev => [...prev, {
      id: generateUniqueId(),
      role: 'user',
      content,
      images
    }]);
  };

  const fetchTask = async (taskId: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/task/${taskId}`);
      const data = await res.json();
      const previousStep = lastReportedStep;
      setCurrentTask(data);
      
      if (data.status === 'completed' && data.video_url && previousStep !== 'completed') {
        addBotMessage(`🎉 Video của bạn đã tạo xong!\n🔗 Link xem và tải xuống: ${data.video_url}`);
        setIsProcessing(false);
        setLastReportedStep('completed');
      } else if (data.status === 'failed' && previousStep !== 'failed') {
        addBotMessage(`❌ Có lỗi xảy ra: ${data.error}`);
        setIsProcessing(false); // Mở khóa ô nhập liệu khi có lỗi
        setLastReportedStep('failed');
      } else if (data.current_step === 'processing_failed' && previousStep !== 'processing_failed') {
        addBotMessage(`❌ Có lỗi nghiêm trọng: ${data.error || 'Không xác định'}`);
        setIsProcessing(false); // Luôn mở khóa khi có lỗi
        setLastReportedStep('processing_failed');
      } else if (data.current_step === 'social_video_generator' && data.status === 'processing' && previousStep !== 'social_video_generator') {
        addBotMessage('⏳ Đang chạy Social Video Generator - tạo nội dung video tối ưu...');
        setLastReportedStep('social_video_generator');
      } else if (data.current_step === 'social_video_generator_completed' && previousStep !== 'social_video_generator_completed') {
        // Hiển thị output chi tiết nếu có
        const socialOutput = data.social_video_generator_completed_output;
        if (socialOutput?.videos) {
          const videoCount = socialOutput.videos.length;
          addBotMessage(`✅ Hoàn thành Social Video Generator!\n📝 Output chi tiết:\n• Tạo được ${videoCount} góc nhìn marketing độc đáo\n• Phù hợp thuật toán ${socialOutput.platform || 'TikTok'}\n• Thời lượng video: ${socialOutput.duration || 15}s`);
        } else {
          addBotMessage(`✅ Hoàn thành Social Video Generator!\n📝 Output: Đã tạo được 2 góc nhìn marketing độc đáo cho sản phẩm, phù hợp thuật toán TikTok.`);
        }
        setLastReportedStep('social_video_generator_completed');
      } else if (data.current_step === 'seedance_video_director' && previousStep !== 'seedance_video_director') {
        addBotMessage('🎬 Đang chạy Seedance Video Director - xây dựng storyboard & kịch bản...');
        setLastReportedStep('seedance_video_director');
      } else if (data.current_step === 'seedance_video_director_completed' && previousStep !== 'seedance_video_director_completed') {
        // Hiển thị output chi tiết nếu có
        const directorOutput = data.seedance_video_director_completed_output;
        if (directorOutput?.processed_videos) {
          const sceneCount = directorOutput.processed_videos[0]?.final_storyboard?.length || 5;
          addBotMessage(`✅ Hoàn thành Seedance Video Director!\n📋 Output chi tiết:\n• Storyboard ${sceneCount} cảnh chi tiết\n• Tối ưu chuẩn Seedance 2.0 API\n• Kịch bản có hook mạnh 3s đầu + CTA rõ ràng`);
        } else {
          addBotMessage(`✅ Hoàn thành Seedance Video Director!\n📋 Output: Kịch bản 15s với hook mạnh 3s đầu, storyboard 5 cảnh chi tiết, CTA rõ ràng.`);
        }
        setLastReportedStep('seedance_video_director_completed');
      } else if (data.current_step === 'seedance2_camera_man' && previousStep !== 'seedance2_camera_man') {
        addBotMessage('🎥 Đang tạo video cuối cùng với Seedance 2.0 API, hãy chờ một chút...');
        setLastReportedStep('seedance2_camera_man');
      } else if (data.current_step === 'waiting_confirmation' && previousStep !== 'waiting_confirmation') {
        addBotMessage(`⏸️ Đang chờ bạn xác nhận thêm thông tin...`);
        setIsProcessing(false); // Mở khóa ô nhập liệu ngay lập tức
        setLastReportedStep('waiting_confirmation');
      }
    } catch (err) {
      console.error('Error fetching task:', err);
    }
  };

  const createVideo = async (brief: string, images: string[]) => {
    const payload: VideoBrief = {
      brief,
      product_images: images,
      ratio: '9:16',
      duration: 15,
      generate_audio: true,
    };

    try {
      const res = await fetch(`${API_BASE}/api/create-video`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      setCurrentTask(data);
    } catch (err) {
      console.error('Error creating video:', err);
      addBotMessage('❌ Có lỗi khi tạo task, vui lòng thử lại!');
      setIsProcessing(false);
    }
  };

  const handleSendMessage = async () => {
    if (!inputValue.trim() && uploadedImages.length === 0) return;
    
    const content = inputValue.trim();
    addUserMessage(content, uploadedImages.length > 0 ? [...uploadedImages] : undefined);
    setInputValue('');
    
    if (!isProcessing) {
      setIsProcessing(true);
      addBotMessage('🤔 Tôi đang xử lý thông tin của bạn...');
      await createVideo(content, uploadedImages);
      setUploadedImages([]);
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files) {
      Array.from(files).forEach(file => {
        const reader = new FileReader();
        reader.onload = (event) => {
          if (event.target?.result) {
            setUploadedImages(prev => [...prev, event.target!.result as string]);
          }
        };
        reader.readAsDataURL(file);
      });
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const removeUploadedImage = (index: number) => {
    setUploadedImages(prev => prev.filter((_, i) => i !== index));
  };

  return (
    <div className="min-h-screen bg-slate-900 flex flex-col">
      {/* Header */}
      <header className="bg-slate-800 border-b border-slate-700 px-6 py-4 shadow-lg">
        <div className="max-w-3xl mx-auto flex items-center gap-3">
          <div className="w-10 h-10 bg-orange-500 rounded-full flex items-center justify-center text-xl">
            🤖
          </div>
          <div>
            <h1 className="text-xl font-bold text-white">Seedance 2.0 Assistant</h1>
            <p className="text-sm text-slate-400">AI tạo video marketing tự động</p>
          </div>
        </div>
      </header>

      {/* Chat Container */}
      <main className="flex-1 max-w-3xl w-full mx-auto p-6 overflow-y-auto">
        <div className="space-y-4">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[80%] rounded-2xl px-4 py-3 whitespace-pre-line ${
                  msg.role === 'user'
                    ? 'bg-orange-500 text-white rounded-br-md'
                    : 'bg-slate-800 text-slate-100 rounded-bl-md'
                }`}
              >
                {msg.images && msg.images.length > 0 && (
                  <div className="grid grid-cols-2 gap-2 mb-3">
                    {msg.images.map((img, i) => (
                      <img key={i} src={img} alt="uploaded" className="rounded-lg w-full h-32 object-cover" />
                    ))}
                  </div>
                )}
                {msg.content}
              </div>
            </div>
          ))}

          {/* Hiển thị ảnh đang chuẩn bị upload */}
          {uploadedImages.length > 0 && (
            <div className="flex justify-end">
              <div className="max-w-[80%] bg-slate-700 rounded-2xl px-4 py-3 rounded-br-md">
                <p className="text-sm text-slate-400 mb-2">Ảnh sẽ gửi:</p>
                <div className="grid grid-cols-3 gap-2">
                  {uploadedImages.map((img, i) => (
                    <div key={i} className="relative">
                      <img src={img} alt="preview" className="rounded-lg w-full h-24 object-cover" />
                      <button
                        onClick={() => removeUploadedImage(i)}
                        className="absolute -top-2 -right-2 w-6 h-6 bg-red-500 rounded-full text-white text-sm"
                      >
                        ×
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </main>

      {/* Input Area */}
      <footer className="bg-slate-800 border-t border-slate-700 px-6 py-4">
        <div className="max-w-3xl mx-auto">
          <div className="flex items-end gap-3">
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileUpload}
              accept="image/*"
              multiple
              className="hidden"
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              className="p-3 bg-slate-700 hover:bg-slate-600 rounded-xl text-white transition"
              title="Upload ảnh"
            >
              📷
            </button>
            <textarea
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Nhập brief của bạn tại đây..."
              className="flex-1 bg-slate-700 border border-slate-600 rounded-xl px-4 py-3 text-white placeholder-slate-400 focus:ring-2 focus:ring-orange-500 focus:border-transparent resize-none"
              rows={3}
              disabled={isProcessing}
            />
            <button
              onClick={handleSendMessage}
              disabled={isProcessing || (!inputValue.trim() && uploadedImages.length === 0)}
              className="p-3 bg-orange-500 hover:bg-orange-600 disabled:bg-slate-600 disabled:cursor-not-allowed rounded-xl text-white transition"
            >
              ➤
            </button>
          </div>
          <p className="text-xs text-slate-500 mt-2 text-center">
            Gửi mô tả sản phẩm + ảnh để AI tạo video marketing TikTok/Reels tự động
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;
