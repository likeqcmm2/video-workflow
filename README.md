# Video Workflow — tiêu đề + script mẫu → video tài liệu hoàn chỉnh

Repo này là "dây chuyền sản xuất" để một AI agent (Claude Code, model Opus) tự làm trọn một video tài liệu
sẵn sàng đăng: phân tích script mẫu → xác định thể loại → nghiên cứu → tìm tư liệu → kịch bản → giọng đọc →
dựng → tự review 2 vòng → xuất MP4 + kịch bản + nguồn + báo cáo.

Chỉ đọc `CLAUDE.md`, `WORKFLOW.md` và tài liệu của giai đoạn đang làm. Ví dụ cú pháp nằm ngay trong
`docs/05-script-format.md`; không cần đọc engine hoặc bộ test để bắt đầu một video mới.

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
docs/                chi tiết từng giai đoạn + Wikimedia + quy tắc tiết kiệm ngữ cảnh
engine/vf/           bộ máy dựng: TTS, timeline, phụ đề, đồ hoạ, render, âm thanh, QA tự động
scripts/             setup.sh, vf (lệnh chính), fetch_fonts.py
templates/           khung project.yaml, script.md, PROGRESS.md, báo cáo...
tests/               smoke test + negative test cho engine (bash tests/run_tests.sh)
```

## Quy tắc vận hành chính

- Render từng chương với phụ đề ở chất lượng cuối; ghép bằng `concat -c copy`. Dùng `render --changed`
  để tái sử dụng chương còn hợp lệ; sửa cấu hình/code chung có thể làm nhiều chương cần render lại.
- Chạy `vf preflight` trước render, xử lý lỗi và xem từng cảnh báo; chạy `vf qa` trên MP4 cuối.
- Thiết kế riêng màu, font, nhịp và chuyển động cho từng video; tỷ lệ tư liệu thật là khoảng cho toàn phim.
- Đồ hoạ/animation ưu tiên **Remotion + SVG**. Python chỉ khi Remotion không đáp ứng yêu cầu cụ thể,
  ghi lý do vào PROGRESS.md. Tích hợp bằng `anim:` / `overlay=anim:` (docs/08).
- Ưu tiên sub-agent xem ảnh scouting/review; khi không khả dụng, agent chính xem theo lô nhỏ và lưu kết quả
  ra file. Dữ liệu thô lưu file, chỉ đưa tóm tắt vào hội thoại.
- Wikimedia dùng thumbnail chuẩn và video chuyển mã qua client chung; bí mật lấy từ biến môi trường.

## Kiểm tra engine

```bash
bash scripts/setup.sh ja
bash tests/run_tests.sh      # không cần API key; dựng video giả lập và kiểm tra QA bắt đủ lỗi
```

## Giới hạn cần biết

- Khi YouTube có tư liệu phù hợp, phải thử tìm và kiểm tra bằng `yt-dlp` trên môi trường hiện tại; không
  giả định nguồn bị chặn vì kinh nghiệm ở máy khác. Xử lý lỗi theo docs/04; không dùng cookie, proxy hay đổi IP
  để vượt chặn.
- AI không tự nghe được âm thanh. Giọng đọc được kiểm tra bằng phiên âm ngược, nhạc và âm lượng được đo bằng số
  liệu; bạn vẫn nên nghe lại trước khi đăng.
- Quyền sử dụng tư liệu nhóm C (bản tin, phim có bản quyền) luôn cần bạn kiểm tra lại (`sources.md`).
