# Chạy IT Helpdesk

Từ thư mục gốc repo, dùng Python 3.10+ có Tkinter (Python Windows thông thường đã có):

```powershell
py -3 -m venv starter_v0/.venv
./starter_v0/.venv/Scripts/python.exe -m pip install -r starter_v0/requirements.txt
```

Nếu chưa có `starter_v0/.env`, copy `.env.example` thành `.env`, rồi điền một key provider. Không ghi đè file `.env` đang có, không commit key. Với môi trường hiện tại đã có `.venv`, có thể chạy thẳng:

```powershell
./starter_v0/.venv/Scripts/python.exe starter_v0/ui.py
```

Mặc định OpenAI / gpt-4o-mini / v4. Provider/model/version nằm trên cửa sổ; đổi cấu hình bằng “Hội thoại mới”. Enter gửi, Shift+Enter xuống dòng. Khung trái là chat, khung phải là version, tool calls, arguments, results và errors. Transcript JSON tự lưu sau mỗi lượt; nút “Lưu lại JSON” thử lưu lại nếu có lỗi filesystem. Dùng dữ liệu giả lập của lab.

## Eval và kiểm tra

Từ thư mục `starter_v0/`:

```powershell
./.venv/Scripts/python.exe scripts/preflight_provider.py --provider openai
./.venv/Scripts/python.exe scripts/collect_evidence.py --version v4
./.venv/Scripts/python.exe scripts/verify_ui_live.py --version v4
./.venv/Scripts/python.exe scripts/test_submission.py
./.venv/Scripts/python.exe scripts/index_evidence.py
./.venv/Scripts/python.exe scripts/check_submission.py
```

Eval và UI live cần mạng/key; phát sinh phí API và có thể tạo ticket **giả lập** trong thư mục local bị Git ignore. Chạy hai script lần lượt để inventory không bị lẫn. `verify_ui_live.py` khởi tạo Tk ở chế độ ẩn và gọi send/poll thật; không phải kiểm thử ảnh. Script có thể trả exit code 1 khi model không đúng kỳ vọng: mở transcript để đọc lỗi, không xóa evidence.

Chạy riêng bộ nhóm:

```powershell
./.venv/Scripts/python.exe run_eval.py --provider openai --model gpt-4o-mini --version v4 --suite group --eval-cases data/eval_group.json
```

`--suite` chỉ là nhãn, `--eval-cases` mới chọn bộ dữ liệu. Với nhiều lượt, evaluator chỉ chấm hành động của lượt cuối; UI transcript mới kiểm tra toàn bộ hội thoại thật. v4 base 28/30, group 9/10, adversarial 9/12, với các giới hạn chi tiết trong [REPORT](artifacts/REPORT.md).

## Evidence

- `runs/`: 4 run base lịch sử v0–v3, 2 run v3 bổ sung, 3 run v4.
- `transcripts/`: 7 hội thoại UI thật; `samples/` chỉ là định dạng mẫu.
- `analysis/`: kiểm kê ticket trước/sau, kết quả UI, unit test, run index và phân tích lỗi.
- `artifacts/snapshots/`: prompt/tools v0 và v3 có hash khớp run; thiếu bản v1/v2 được nêu rõ trong báo cáo.
- `artifacts/version_log.csv`: kết quả có thể đối chiếu; không bịa giả thuyết lịch sử chưa biết.

Nếu gặp `ModuleNotFoundError: yaml`, hãy dùng Python trong `.venv` hoặc cài `requirements.txt` vào đúng Python đang chạy. Nếu gặp lỗi API, kiểm tra key/provider và preflight; không đăng key lên chat hoặc Git.
