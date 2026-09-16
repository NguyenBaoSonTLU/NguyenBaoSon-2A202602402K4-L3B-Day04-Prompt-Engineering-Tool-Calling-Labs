# BÀI LÀM CÁ NHÂN — Day04, K4-L3B

## Thông tin bài nộp
# Day 04 Lab v3 Report — Trợ lý IT Helpdesk

- Lĩnh vực tự chọn: IT Helpdesk, sử dụng dữ liệu công ty giả lập.
- Nhiệm vụ và luồng cơ bản đã chốt trước v0:
  Tiếp nhận yêu cầu hỗ trợ IT; kiểm tra tình trạng dịch vụ, thiết bị,
  tra cứu hướng dẫn và thông tin nhân viên bằng công cụ phù hợp.
  Hỏi lại khi thiếu thông tin; chỉ tạo ticket sau khi người dùng
  xác nhận rõ ràng; cập nhật hoặc hủy thao tác theo yêu cầu mới nhất.
- Đường dẫn bộ 30 câu cơ bản: starter_v0/data/eval_base.json.
- Đường dẫn bộ 12 câu an toàn: [đường dẫn thực tế].
- Commit chốt bộ trước v0: [commit hash thực tế].
- Chức năng mở rộng ngoài luồng cơ bản: [ghi chức năng hoặc “Không có”].

## Cá nhân

- Họ tên: Nguyễn Bảo Sơn
- MSSV: 2A202602402
- GitHub username: NguyenBaorSonTLU 
- Vai trò: Thực hiện prompt engineering, rà soát khai báo công cụ,
  chạy đánh giá, xây dựng UI và tổng hợp báo cáo.

## Tổng quan bài làm

Xây dựng trợ lý IT Helpdesk dùng dữ liệu công ty giả lập. Agent có thể định tuyến yêu cầu tới đúng tool để kiểm tra service, thiết bị và tài khoản; tìm hướng dẫn kỹ thuật hoặc policy; hỏi lại khi thiếu thông tin; xử lý hội thoại nhiều lượt, đính chính và hủy yêu cầu; đồng thời tạo ticket local sau khi người dùng xác nhận.

Các tool chính gồm `clarify`, `search_kb`, `check_service_status`, `inspect_device`, `lookup_user`, `format_incident_report`, `policy`, `create_ticket` và `search_device_info`.

## Kết quả và bằng chứng lịch sử từ commit d0deff4

- Bộ base v3: **30/30 case, đạt 100%**, `provider_error_cases=0`, `measured_cases=30`.
- Tiến triển qua các phiên bản: v0 đạt 21/30 (70%); v1 đạt 29/30 (96,67%); v2 đạt 29/30 (96,67%); v3 đạt 30/30 (100%).
- Bộ 10 case cá nhân: **7/10 pass**. Các case chưa đạt là G01, G03 và G10.
- Bộ adversarial: **6/12 pass**. A01 và A05 đạt; A03, A10 và A12 cho thấy còn lỗi về confirmation giả mạo, stale confirmation và việc chặn internal ID trước external search.
- Bộ extension built-in: 5/10 pass; không có bonus tool tự xây.
- Có UI Streamlit tại [`starter_v0/app.py`](starter_v0/app.py), hiển thị lịch sử chat, phiên bản artifact, tool call, arguments và tool results.
  ![alt text](image.png)
- Có transcript, run JSON, version log, prompt, tool schema và report trong thư mục `starter_v0`.

Evidence chính:

- [Report](starter_v0/artifacts/REPORT.md)
- [System prompt](starter_v0/artifacts/system_prompt.md)
- [Tool declarations](starter_v0/artifacts/tools.yaml)
- [Version log](starter_v0/artifacts/version_log.csv)
- [Eval cá nhân](starter_v0/data/eval_group.json)
- [Run base v3](starter_v0/runs/v3_B_base_openai_20260915T201001847232.json)
- [Run group](starter_v0/runs/v3_B_group_openai_20260915T202222480947.json)
- [Run adversarial](starter_v0/runs/v3_B_adversarial_openai_20260915T202527466754.json)

## Công việc đã thực hiện

- Phân tích lỗi từ run v0 và xác định các lỗi về chọn tool, thiếu thông tin, argument, multi-turn và confirmation boundary.
- Cải thiện `system_prompt.md` ở v1/v2: bổ sung routing, quy tắc gọi `clarify`, mapping argument, sửa/hủy, xác nhận hành động và trust boundary/chống prompt injection.
- Cải thiện `tools.yaml` ở v3: bắt buộc `search_kb.category` và bổ sung mapping cho Outlook/email, Wi-Fi và VPN.
- Viết và chạy bộ `eval_group.json` gồm 5 case một lượt và 5 case nhiều lượt.
- Chạy các phiên bản v0–v3, so sánh metric và ghi lại giả thuyết, hash artifact và đường dẫn run trong `version_log.csv`.
- Hoàn thiện UI Streamlit, transcript và `REPORT.md`.

## Khó khăn, cách xử lý và giới hạn

- Ở v0, agent từng dùng các giá trị mơ hồ như `laptop`, `Sales` hoặc `demo` làm ID/environment; đã bổ sung quy tắc bắt buộc hỏi lại bằng `clarify`.
- Agent từng gọi thừa `inspect_device` sau `lookup_user`; đã ghi rõ không gọi lại khi kết quả trước đã có danh sách thiết bị, trừ khi người dùng yêu cầu kiểm tra.
- Agent từng tự đặt `confirmed=true` hoặc gọi action trước khi xác nhận; prompt đã yêu cầu xác nhận rõ theo đúng payload hiện tại.
- Vẫn còn lỗi stale confirmation ở A10 và lỗi external search với internal ID ở A12. Nếu có thêm một vòng, cần chuyển confirmation và chặn dữ liệu nhạy cảm vào application/orchestrator thay vì chỉ dựa vào prompt.
- Các ticket local phát sinh từ eval cần được loại khỏi commit theo quy định; không commit `.env`, API key, cache, dữ liệu thật hoặc thư mục ticket.

## Điều đã học

- Cần đánh giá cả routing, arguments, tool results và side effect; chỉ nhìn PASS/FAIL chưa đủ để kết luận agent an toàn.
- Prompt cần quy định rõ điều kiện hỏi lại, mapping tham số, correction/cancellation và ranh giới xác nhận hành động.
- Tool schema có thể cải thiện đáng kể độ chính xác khi biến quan trọng được đánh dấu bắt buộc và có hướng dẫn mapping cụ thể.
- Phải giữ nguyên bộ case giữa các phiên bản để so sánh v0–v3 có ý nghĩa.

## AI và công cụ đã sử dụng

- OpenAI API với model `gpt-4o-mini`: chạy agent và các bộ đánh giá.
- Python và các script trong `starter_v0`: chạy eval, tạo run/transcript và kiểm tra metric.
- Streamlit: xây dựng giao diện chat và hiển thị trace tool.
- Git/GitHub: quản lý source, evidence và lịch sử thay đổi.
- Cách kiểm tra: đối chiếu `provider_error_cases`/`measured_cases`, đọc tool arguments và tool results, kiểm tra transcript và rà soát side effect trên filesystem.

## Tự đánh giá kế thừa — cần người nộp xác nhận hoặc viết lại

- Thay đổi hiệu quả nhất: bổ sung quy tắc routing/clarify trong prompt và bắt buộc `search_kb.category`; kết quả base tăng từ 70% ở v0 lên 100% ở v3.
- Điểm còn có thể cải thiện: xác nhận phải được ràng buộc ở tầng application/orchestrator; cần sửa ba nhóm lỗi adversarial còn lại và cải thiện các case G01, G03, G10.
