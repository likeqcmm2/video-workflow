# Báo cáo cuối — チャレンジャー号爆発事故の真相

**File:** `out/video.mp4` — H.264 High, 1920×1080, 30 fps, yuv420p, AAC 48 kHz stereo 192 kbps, faststart.
- Thời lượng: **32:35,8** (1955,8 s). Video và audio dài bằng nhau; có 58.674 khung hình.
- Âm lượng tích hợp −16,1 LUFS, true peak −1,4 dBTP.

## Số liệu
- **Lời dẫn: 10.351 ký tự** (đếm bằng `src/count_chars.py` trên văn bản TTS, đã bỏ khoảng trắng). Đạt ngưỡng ≥ 10.000.
  - Hook: 465 ký tự / 12 câu. Mẫu là 421 ký tự, khoảng cho phép 358–484 ký tự. Hook đã khoá.
  - Body: 9.886 ký tự, 8 chương.
- **Giọng đọc:** 229 cảnh, Gemini `gemini-3.8-flash-tts`, giọng Arlo.
  - Tổng thời lượng giọng: **1.795,0 s (29:55)**.
  - Kiểm tra ngược bằng ASR: độ giống trung bình 0,990, thấp nhất 0,857 (S314; chỉ khác cách viết kanji/kana).
- **Tỉ lệ hình ảnh theo thời lượng:**
  - Tư liệu thật **59,1%**: video 25,3%, ảnh 33,8%.
  - Đồ hoạ giải thích và thẻ trích dẫn **39,3%**.
  - Thẻ chương và màn kết 1,7%.

## Thể loại và hướng hình ảnh
- **Thể loại:** tài liệu thảm hoạ / chuyện có thật, giọng trầm và nghiêm.
- **Hình ảnh chủ đạo:** tư liệu thật, gồm:
  - băng VTV‑26 của Uỷ ban Rogers;
  - ảnh NASA;
  - phim NASA về phi hành đoàn và McAuliffe;
  - diễn văn của Reagan.
- **Đồ hoạ:** tông tối "hồ sơ điều tra", nền than chì, nhấn bằng màu đỏ gỉ và xanh băng.
  - Gồm sơ đồ khớp nối O‑ring, biểu đồ nhiệt độ/hư hại theo dữ liệu Dalal 1989, bản đồ cuộc gọi đêm 27/1, dòng thời gian, và tài liệu tái hiện có ghi 「再現」.
  - Chương 2–3 có nhiều đồ hoạ nhất, vì nội dung là phần giải thích kỹ thuật.
- **Nhạc:** Kevin MacLeod, CC BY 4.0. Mỗi chương một bản; nhạc tự giảm khi có lời dẫn.
- **Phụ đề:** chữ Nhật được đốt cứng vào hình. Số viết bằng chữ số, ngắt ở chỗ hợp nghĩa và khớp với từng câu thoại.

## Bài học từ script mẫu (đã áp dụng)
- **Hook:** mở bằng cảnh cụ thể có ngày giờ; tiếp theo một câu ngắn gây tò mò, một câu trích dẫn gây sốc đứng riêng, con số thiệt hại, câu hỏi なぜ〜のでしょうか, rồi 「今回は〜真相を解き明かしていきます」.
- **Văn phong:** toàn bộ です・ます. Hay dùng 「だが」 đầu câu và kết nhấn bằng 「〜のです」. Sau mỗi dữ kiện lớn có một câu đánh giá ngắn.
- **Giải thích thuật ngữ** ngay tại chỗ, theo mẫu 「Oリングとは、〜のことです」.
- **Kết chương:** chương nào cũng kết bằng một câu móc sang chương sau.
- **Đối chiếu hai số phận:** người lên tiếng (McDonald, Boisjoly, Ebeling) và người không bị truy cứu.
- **Kết bài:** rút ra bài học chung, nối với hiện tại (Columbia, rồi các tổ chức ngày nay) và để lại câu hỏi mở. Không kêu gọi like hay đăng ký.

## Những gì đã sửa qua 2 vòng review
- **Vòng 1** (từng chương, 1 khung mỗi 2,5 s, có phụ đề):
  - **Khả năng đọc chữ:** thêm lớp tối dưới phụ đề và nền cho lower‑third. Ảnh không còn tràn vào vùng phụ đề. Chú thích tài liệu và ghi chú trên dòng thời gian được dời vào vùng an toàn.
  - **Phụ đề:** sửa các chỗ ngắt giữa từ (から, た, 人, キルミンスター, うきは…) và gộp các mẩu thừa. Ẩn phụ đề ở các thẻ trích dẫn để chữ không bị lặp.
  - **Ảnh sai nội dung:** ảnh Commons "Rogers‑report‑front‑page" thực ra là bìa phiên điều trần Thượng viện, nên đã bỏ.
  - **Stamp sai:**
    - Bỏ stamp ngày sai ở S517.
    - Bỏ stamp "ユタ州" đặt lên cảnh Florida.
    - Ảnh MSFC (S311) có ghi 「写真は2013年」.
  - **Cảnh lỗi:**
    - S809 bị thẻ trống, nay thay bằng footage bọt cách nhiệt đập vào cánh Columbia (NASA, PD, chiếu chậm).
    - S010 dùng lại ảnh băng ở cảnh khác, nay đổi sang ảnh khói lửa rò ra từ khớp nối.
    - S505 và S507 dùng video diễn văn Reagan (CC BY 3.0).
    - S615 có khoảng 1 s đen ở đầu shot, đã bỏ.
  - **Đồ hoạ:** sơ đồ phân cấp "levels" có chữ tràn khung, đã mở rộng khung.
  - **Ghi công:** sửa ghi công CC BY‑SA cho ảnh đài tưởng niệm ở KSC.
- **Vòng 2** (toàn bộ `out/video.mp4`, 1 khung mỗi 3 s, cùng ffprobe và loudnorm):
  - S435 bị khoảng 1,5 s đen do băng gốc mờ dần về đen. Đã thêm điểm cắt; shot nay được làm chậm khoảng 0,77×.
  - Không thấy lỗi nào khác về phong cách, chữ đè lên mặt người, hay ghi nguồn.

## Các điểm người dùng nên kiểm tra
1. **Quyền sử dụng** (chi tiết ở `sources.md`, các mục có cờ "CẦN KIỂM TRA QUYỀN"):
   - **Băng VTV‑26** (Internet Archive, bản số hoá của A/V Geeks): nội dung là tư liệu chính phủ Mỹ nên rủi ro thấp. Tuy vậy trang gốc có mời mua bản chất lượng cao, nên cần xác nhận.
   - **Ảnh "Richard Feynman 1988"**: Commons ghi là phạm vi công cộng nhưng không rõ tác giả (ảnh Caltech). Nên xác minh.
   - **Các file bắt buộc ghi công:**
     - Video Reagan: CC BY 3.0.
     - Ảnh sân bay Kona: CC BY 2.0.
     - Ảnh Little Tokyo và ảnh đài tưởng niệm KSC: CC BY‑SA 3.0.
     - Nhạc: CC BY 4.0.
     - Trên màn hình đã có ghi công. Khi đăng video, hãy dán thêm `out/credits_for_description.txt` vào phần mô tả.
2. **Âm thanh:** giọng Arlo đọc ổn định. Vài tên riêng tiếng Anh được đọc theo cách phiên âm Nhật (ボイジョリー, キルミンスター…). Nhạc nền nhỏ hơn giọng; ở chương 4 nhạc được cắt hẳn trước khoảnh khắc tàu vỡ (S429).
3. **Nguồn yếu:**
   - Câu "không ai bị truy cứu hình sự" dựa trên việc không thấy ghi nhận nào trong các nguồn đã đọc.
   - Con số 85% người Mỹ biết tin trong vòng 1 giờ chỉ đến từ một khảo sát duy nhất.
   - Các câu trích lời Mulloy, Mason và Ebeling là lời kể lại qua lời khai hoặc phỏng vấn.
4. **Hình chỉ khớp tương đối với lời dẫn:**
   - S409: gia đình McAuliffe trên khán đài, nhưng hình là McAuliffe bước vào khoang.
   - S716–S717: thư gửi Ebeling, nhưng hình là cảnh bệ phóng.
   - Cảnh Ebeling: dùng shot bệ phóng ban đêm.
   - Cảnh Feynman thả O‑ring vào nước đá: là minh hoạ tái hiện, vì không có footage.
   - Footage Columbia: có số khung hình gốc ("Frame NNNN") nằm trong hình.
5. **Khác với mẫu:**
   - Video này có thẻ chương (第1章…第8章), còn mẫu chuyển chương bằng lời.
   - Có thêm chương 8 về Columbia và phần nối sang hiện tại.
   - Nhịp đồ hoạ ở chương 2–3 dày hơn, vì nội dung kỹ thuật cần giải thích bằng hình.
6. **Wikimedia:** tất cả request đều qua `src/wm_client.py`. Tổng cộng 165 request: 125 tới API, 40 tải file, 8 lần bị 429 và đều đã chờ đúng thời gian yêu cầu. Bản gốc trên upload.wikimedia.org bị chặn, nên đã dùng thumbnail và bản chuyển mã chuẩn. Chi tiết ở `PROGRESS.md`.

## File đầu ra
- `out/video.mp4`
- `script.md`
- `sources.md`
- `PROGRESS.md`
- `out/credits_for_description.txt`
- `out/review/` (các trang ảnh rà soát)
