# TEAM — Day04, K4-L3B

## Thông tin bài nộp

- Tên hiển thị theo repo hiện tại: **HayUongNuoc** — cần nhóm xác nhận.
- Đại diện / MSSV: **chưa được cung cấp**.
- Repo hiện tại: `K4-L3-DAY04-HayUongNuoc-PromptEngineeringToolCalling`.
- Remote: https://github.com/HongNhung-0204/K4-L3-DAY04-HayUongNuoc-PromptEngineeringToolCalling
- Nhánh làm việc: `main`. Commit nộp chính thức: chưa chốt vì còn thông tin cá nhân/checkout.
- Deadline: cần đối chiếu thông báo lớp. Quy tắc mặc định là 23:59 ngày học, Asia/Ho_Chi_Minh; các run gốc mang ngày 2026-09-15, lượt bổ sung mang ngày 2026-09-16. Không sửa ngày để che bổ sung muộn.

## Thành viên

Chưa nhận được họ tên, MSSV, GitHub và phân công của từng người. Không suy ra thành viên từ chủ remote hoặc cấu hình Git của máy. Trước khi nộp, từng người cần bổ sung các trường này và dẫn commit kỹ thuật thật.

## Công việc có evidence

- UI Tkinter: `starter_v0/ui.py`, cấu hình provider/model/version, hiển thị trace, lưu hội thoại và xử lý lưu lại.
- Bộ nhóm: `starter_v0/data/eval_group.json`, 5 case một lượt + 5 nhiều lượt.
- Artifact v4: `starter_v0/artifacts/system_prompt.md`, `tools.yaml`, cùng snapshot v0/v3.
- Thu thập thật: `starter_v0/scripts/collect_evidence.py`, `verify_ui_live.py`; run JSON và 7 transcript.
- Sửa giữ trace khi provider lỗi sau tool: `starter_v0/chat.py`, kiểm thử regression tại `scripts/test_submission.py`.
- Tổng hợp evidence: `scripts/index_evidence.py`, `scripts/check_submission.py`, `artifacts/version_log.csv`, `artifacts/REPORT.md`, README.

Các phần hoàn thiện trên có **Codex hỗ trợ thực hiện theo yêu cầu của người dùng**. Chưa phân bổ quyền tác giả/đóng góp cho từng người khi chưa có xác nhận. Không dùng cấu hình tác giả Git làm bằng chứng ai đã tự thực hiện thao tác hoặc hiểu bài.

## Nhận xét chung dựa trên evidence

Base tăng từ 21/30 ở v0 lên 28/30 ở v3; v4 giữ 28/30. Group v4 đạt 9/10. Adversarial tăng từ 6/12 ở v3 lên 9/12 ở v4; số ticket phát sinh trong safety giảm từ 4 xuống 0 trong các run đã quan sát. Chi tiết và giới hạn nằm trong [REPORT](starter_v0/artifacts/REPORT.md).

Thay đổi v4 có evidence cải thiện confirmation nhưng chưa giải quyết scope correction; model vẫn có lúc dùng sai category/clarify và không theo output JSON. Chưa có snapshot/nhật ký v1–v2 để xác nhận nguyên nhân cải thiện lịch sử. Nhóm cần tự kiểm tra lại các điểm này trước khi nhận xét cá nhân hoặc trình bày demo.

Phân công và cách tích hợp: chờ thành viên cung cấp thông tin thực tế. Evidence kỹ thuật được lưu tập trung trong `starter_v0/`; không lấy `samples/` làm kết quả thật.

## INDIVIDUAL — mỗi thành viên tự hoàn thiện

Theo [RULES.md](RULES.md), mỗi người tự viết phần này và dẫn đóng góp có thể đối chiếu. Chưa có nội dung tự nhận xét do người học cung cấp, nên các dòng sau là trường cần điền, **không phải lời tự đánh giá đã hoàn thành**.

### Họ tên / MSSV / GitHub: cần điền

- Phần việc đã trực tiếp thực hiện, file và commit/PR thực: cần điền.
- Quyết định đã đưa ra, khó khăn thực tế và cách xử lý: cần người học viết.
- Điều đã học và cách tự kiểm tra hiểu biết: cần người học viết.
- AI/công cụ: Codex đã hỗ trợ code, tạo case, chạy kiểm tra và tổng hợp báo cáo; bổ sung thao tác người học đã tự chạy/đọc/kiểm tra.
- Thời điểm tự nộp URL trên VLearn, URL đã lưu: chưa xác nhận đã nộp.

Sao chép mục này cho các thành viên còn lại; không tạo commit giả danh hay điền trải nghiệm thay cho người khác.
