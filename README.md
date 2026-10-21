# Video Workflow — tiêu đề + script mẫu → video tài liệu hoàn chỉnh

Repo này là "dây chuyền sản xuất" để một AI agent (Claude Code, model Opus) tự làm trọn một video tài liệu
sẵn sàng đăng: phân tích script mẫu → xác định thể loại → nghiên cứu → tìm tư liệu → kịch bản → giọng đọc →
dựng → tự review 2 vòng → xuất MP4 + kịch bản + nguồn + báo cáo.

Chuẩn chất lượng là video mẫu trong `examples/challenger/` (phim tài liệu tiếng Nhật 32 phút). Mọi bài học
từ lần sản xuất đó (post-mortem) đã được biến thành luật, công cụ và bước kiểm tra tự động trong repo.

## Cách dùng (mỗi video mới)

1. Mở Claude Code (web, app hoặc CLI) với môi trường đã cấu hình biến bí mật (xem "Cài đặt một lần").
2. Gửi tin nhắn kiểu dưới đây, kèm file script mẫu:

```
Dùng workflow trong repo https://github.com/<owner>/<repo> để làm video.
Tiêu đề: <tiêu đề video>
Script mẫu: (file đính kèm)
Ngôn ngữ: Japanese          (tuỳ chọn, mặc định ja)
Độ dài lời đọc tối thiểu: 10000 ký tự    (tuỳ chọn)
Mức tư liệu có bản quyền: CÂN BẰNG       (AN TOÀN / CÂN BẰNG / TỐI ĐA)
Hình ảnh mạnh: KHÔNG
```

AI sẽ clone repo, đọc `CLAUDE.md` → `WORKFLOW.md`, rồi tự làm hết mà không hỏi lại, trừ khi bị chặn hẳn
(ví dụ thiếu API key). Kết quả nằm trong `projects/<slug>/`:

- `out/video.mp4`
- `script.md` (hồ sơ văn phong + hướng đạo diễn + hệ thống thiết kế + kịch bản)
- `sources.md` (từng tư liệu, giấy phép, mục **CẦN KIỂM TRA QUYỀN**; bảng đối chiếu nguồn cho từng dữ kiện)
- `REPORT.md` (báo cáo cuối)

Muốn upload lên Drive thì gửi thêm file `rclone.conf` và dặn upload.

## Cài đặt một lần

**Biến bí mật** — khai báo trong phần cài đặt Environment của Claude Code. Không dán vào tin nhắn, không commit:

| Biến | Dùng cho | Bắt buộc |
|---|---|---|
| `GEMINI_API_KEY` | giọng đọc Gemini TTS + kiểm tra ngược ASR | có |
| `WIKIMEDIA_USER_AGENT` | ví dụ `VideoMakerAgent/1.0 (https://commons.wikimedia.org/wiki/User:<tên>; bot)` | nên có |
| `WIKIMEDIA_BOT_USER`, `WIKIMEDIA_BOT_PASSWORD` | Bot Password của Wikimedia (`User@BotName`) | không (thiếu thì chạy chế độ ẩn danh, chậm hơn) |

**Network**: môi trường cần ra được internet tới Google API, Wikimedia, NASA, Internet Archive, Google Fonts,
naciscdn.org (bản đồ) và incompetech.com (nhạc).

AI tự chạy `bash scripts/setup.sh <ngôn ngữ>` để cài ffmpeg, thư viện Python, font và dữ liệu bản đồ.

## Cấu trúc

```
CLAUDE.md            điểm vào cho AI (tự động được nạp)
WORKFLOW.md          12 giai đoạn, mỗi giai đoạn có cổng kiểm tra (gate)
docs/                chi tiết từng giai đoạn + Wikimedia + bài học + quy tắc tiết kiệm ngữ cảnh
engine/vf/           bộ máy dựng: TTS, timeline, phụ đề, đồ hoạ, render, âm thanh, QA tự động
scripts/             setup.sh, vf (lệnh chính), fetch_fonts.py
templates/           khung project.yaml, script.md, PROGRESS.md, báo cáo...
examples/challenger/ video mẫu: cấu hình, kịch bản, đồ hoạ riêng, nguồn, báo cáo
tests/               smoke test + negative test cho engine (bash tests/run_tests.sh)
```

## Những gì đã cải tiến so với lần làm video Challenger

- **Xuất video**: không còn bước encode lại cả phim. Mỗi chương render một lần ở chất lượng cuối (phụ đề đốt
  sẵn), ghép bằng `concat -c copy` trong ~1 phút. Sửa 1 lỗi chỉ render lại đúng chương bị ảnh hưởng (tự phát
  hiện bằng hash). Lần trước: 2 lần xuất × 67 phút + 39 lượt render chương.
- **QA tự động trước khi render** (`vf preflight`) bắt các lỗi mà lần trước chỉ phát hiện bằng mắt sau khi
  render: màn hình đen/mờ dần trong footage, thẻ trống, chữ tràn khung, chữ đè vùng phụ đề, thiếu ghi nguồn,
  giọng đọc lỗi thời sau khi sửa kịch bản, ngắt dòng phụ đề sai, footage bị làm chậm quá mức.
- **Phụ đề tiếng Nhật** ngắt dòng bằng BudouX (không cắt giữa từ).
- **Review ảnh do sub-agent làm**, ngữ cảnh chính không bị phình (lần trước 119 ảnh nằm trong ngữ cảnh).
- **Wikimedia**: thumbnail chuẩn + bản video chuyển mã ngay từ đầu (file gốc bị 429).
- **Bí mật** chỉ qua biến môi trường.
- **Tổng quát**: đa thể loại, đa ngôn ngữ (ja, zh, ko, en, vi…). Repo **chỉ ghi kỹ thuật và các lỗi kỹ thuật
  đã gặp**, không có preset màu, không có template đồ hoạ, không có font/chuyển động mặc định: AI tự thiết kế
  màu, chữ, đồ hoạ, animation cho từng video theo thể loại, thời kỳ, chất liệu. Preflight báo lỗi nếu thiếu
  quyết định thiết kế nào.
- **Tỷ lệ footage thật / đồ hoạ** là khoảng min–max do AI chọn theo thể loại (`director.real_pct`), kiểm tra cả
  phim và từng chương; chương nào cần lệch (ví dụ cơ chế không ai quay được) thì ghi ngoại lệ kèm lý do.
- **Animation ngoài** (Manim, Remotion, Blender, Three.js…) dùng được như clip `anim:`, kể cả lớp phủ có kênh
  alpha; chuyển cảnh fade/dissolve; nhiều bảng màu (grade) theo chương hoặc từng shot.

Chi tiết: `docs/lessons-learned.md`.

## Kiểm tra engine

```bash
bash scripts/setup.sh ja
bash tests/run_tests.sh      # không cần API key; dựng video giả lập và kiểm tra QA bắt đủ lỗi
```

## Giới hạn cần biết

- YouTube thường chặn IP của máy chủ cloud nên không tải được. Workflow không vượt chặn (không dùng cookie,
  proxy hay đổi IP).
- AI không tự nghe được âm thanh. Giọng đọc được kiểm tra bằng phiên âm ngược, nhạc và âm lượng được đo bằng số
  liệu; bạn vẫn nên nghe lại trước khi đăng.
- Quyền sử dụng tư liệu nhóm C (bản tin, phim có bản quyền) luôn cần bạn kiểm tra lại (`sources.md`).
