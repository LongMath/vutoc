# Gia phả Vũ tộc — ứng dụng Streamlit

Xem cây phả hệ họ Vũ và thêm/sửa/xóa thông tin từng người, có bước xác nhận
trước khi lưu.

## Chạy thử ở máy tính của bạn

```bash
pip install -r requirements.txt
streamlit run app.py
```

Trình duyệt sẽ tự mở `http://localhost:8501`.

## Lưu ý quan trọng về dữ liệu

Toàn bộ cây phả hệ nằm trong file `gia_pha_tree.json` (cùng thư mục với
`app.py`). Khi bạn Thêm/Sửa/Xóa trong app:

- **Chạy ở máy mình (`streamlit run app.py`)**: app tự ghi đè lại
  `gia_pha_tree.json`, thay đổi được lưu thật.
- **Chạy trên Streamlit Community Cloud**: ổ đĩa của app sẽ bị xóa mỗi khi
  app khởi động lại (mất mạng, cập nhật code, ngủ do không ai dùng...), nên
  **thay đổi có thể mất** nếu chỉ dựa vào việc ghi file trên server. Vì vậy
  sau khi sửa xong, luôn bấm nút **"⬇️ Tải xuống gia_pha_tree.json hiện tại"**
  ở tab Xem cây, rồi thay file cũ trong repo GitHub bằng file vừa tải (xem
  hướng dẫn cập nhật bên dưới) để lưu vĩnh viễn.

## Cấu trúc dữ liệu (gia_pha_tree.json)

Mỗi người là một object:

```json
{
  "ten": "Tên người",
  "doi": 5,
  "do_tin_cay": "cao",
  "con": [ ...danh sách con, cùng cấu trúc... ],
  "ghi_chu": "không bắt buộc"
}
```

`do_tin_cay` nhận 1 trong 3 giá trị: `"cao"` (đã xác nhận), `"trungbinh"`
(khá chắc), `"thap"` (cần kiểm tra).

## Cập nhật file trên GitHub sau khi sửa trong app

1. Tải file mới bằng nút trong app.
2. Vào repo trên GitHub → mở file `gia_pha_tree.json` → bấm biểu tượng bút
   chì (Edit) → xóa hết nội dung cũ, dán nội dung file mới vào → Commit.
3. Streamlit Community Cloud sẽ tự động phát hiện commit mới và khởi động
   lại app với dữ liệu mới trong vài chục giây.
