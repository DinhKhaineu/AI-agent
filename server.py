from fastmcp import FastMCP
# Giả sử bạn đã lưu class NoteManager trong file note_manager.py
from main import NoteManager 

# Khởi tạo MCP Server và kết nối với Vault
mcp = FastMCP("Obsidian-Knowledge-Agent")

OBSIDIAN_VAULT= r"C:\stuff\NCKH"
manager = NoteManager(OBSIDIAN_VAULT)

@mcp.tool()
def search_vault(keyword: str) -> list[str]:
    """
    Tìm kiếm ghi chú theo từ khóa trong toàn bộ Obsidian vault.
    Trả về danh sách tên các ghi chú khớp với từ khóa.
    """
    results = manager.search_notes(keyword)
    return [p.name for p in results]

@mcp.tool()
def read_note_content(note_name: str) -> str:
    """
    Đọc toàn bộ nội dung văn bản của một ghi chú cụ thể.
    Ví dụ note_name: "Causal Inference" hoặc "Causal Inference.md".
    """
    target = f"{note_name}.md" if not note_name.endswith(".md") else note_name
    try:
        return manager.read_note(target)
    except FileNotFoundError:
        return f"Lỗi: Không tìm thấy ghi chú '{target}'"

@mcp.tool()
def get_note_metadata_and_links(note_name: str) -> dict:
    """
    Trích xuất cấu trúc của một ghi chú bao gồm: tags, headings, và các wikilinks (liên kết một chiều).
    Sử dụng công cụ này để hiểu bố cục của một khái niệm trước khi đọc chi tiết.
    """
    target = f"{note_name}.md" if not note_name.endswith(".md") else note_name
    try:
        parsed = manager.parse_note(target)
        # Bỏ phần content dài dòng ra để LLM không bị quá tải ngữ cảnh
        parsed.pop("content", None) 
        return parsed
    except FileNotFoundError:
        return {"error": f"Không tìm thấy ghi chú '{target}'"}

@mcp.tool()
def find_concept_relationships(note_name: str) -> dict:
    """
    Khám phá đồ thị tri thức 2 chiều của một khái niệm.
    Trả về các ghi chú mà nó trỏ tới (outgoing) và các ghi chú trỏ ngược về nó (backlinks).
    """
    clean_name = note_name.replace(".md", "")
    return {
        "concept": clean_name,
        "outgoing_links": manager.find_outgoing_links(clean_name),
        "backlinks": manager.find_backlinks(clean_name),
        "all_related": manager.find_related_notes(clean_name)
    }

if __name__ == "__main__":
    # Lệnh này cho phép chạy server trực tiếp
    mcp.run()