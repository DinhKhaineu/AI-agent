# note_manager.py
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Set, Union
import frontmatter

WIKILINK_PATTERN = re.compile(r"\[\[([^\]]+)\]\]")
HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+)$")
ATTACHMENT_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", 
    ".pdf", ".mp3", ".mp4", ".canvas"
}


def resolve_safe_path(vault_root: Path, input_path: Union[str, Path]) -> Path:
    path = Path(input_path)
    if not path.is_absolute():
        path = vault_root / path
    full_path = path.resolve()
    if not full_path.is_relative_to(vault_root):
        raise PermissionError(f"Access to {full_path} is denied. Path traversal detected.")
    return full_path


class NoteManager:
    def __init__(self, vault_path: Union[str, Path]):
        self.vault = Path(vault_path).resolve()
        self.vault.mkdir(parents=True, exist_ok=True)

    def list_notes(self, subfolder: Union[str, Path] = "") -> List[Path]:
        target_dir = resolve_safe_path(self.vault, subfolder)
        if not target_dir.is_dir():
            return []
        return list(target_dir.rglob("*.md"))

    def read_note(self, file_path: Union[str, Path]) -> str:
        path = resolve_safe_path(self.vault, file_path)
        return path.read_text(encoding="utf-8")

    def create_note(self, file_path: Union[str, Path], content: str = "") -> None:
        path = resolve_safe_path(self.vault, file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def update_note(self, file_path: Union[str, Path], content: str) -> None:
        path = resolve_safe_path(self.vault, file_path)
        if not path.exists():
            self.create_note(path, content)
            return
        with path.open("a", encoding="utf-8") as f:
            if path.stat().st_size > 0 and not path.read_text(encoding="utf-8").endswith("\n"):
                f.write("\n")
            f.write(content)

    def delete_note(self, file_path: Union[str, Path]) -> None:
        path = resolve_safe_path(self.vault, file_path)
        if path.exists() and path.is_file():
            path.unlink()

    def parse_note(self, relative_path: Union[str, Path]) -> Dict[str, Any]:
        path = resolve_safe_path(self.vault, relative_path)
        post = frontmatter.load(path)

        raw_links = WIKILINK_PATTERN.findall(post.content)
        links = []
        for link in raw_links:
            clean_target = link.split("|")[0].split("#")[0].strip()
            if any(clean_target.lower().endswith(ext) for ext in ATTACHMENT_EXTENSIONS):
                continue
            if clean_target:
                links.append(clean_target)

        headings = []
        in_code_block = False
        for line in post.content.splitlines():
            line_stripped = line.strip()
            if line_stripped.startswith("```"):
                in_code_block = not in_code_block
                continue
            if not in_code_block:
                match = HEADING_PATTERN.match(line_stripped)
                if match:
                    headings.append(match.group(2).strip())

        tags = post.metadata.get("tags") or []
        if isinstance(tags, str):
            tags = [tags]

        return {
            "path": str(path.relative_to(self.vault)),
            "title": post.metadata.get("title", path.stem),
            "metadata": post.metadata,
            "tags": tags,
            "headings": headings,
            "links": links,
            "content": post.content,
        }

    def search_notes(self, keyword: str) -> List[Path]:
        keyword_lower = keyword.lower()
        results = []
        for note in self.list_notes():
            try:
                if keyword_lower in note.name.lower() or keyword_lower in note.read_text(encoding="utf-8").lower():
                    results.append(note)
            except (UnicodeDecodeError, PermissionError):
                continue
        return results

    def build_graph(self) -> Dict[str, Any]:
        forward_graph: Dict[str, Set[str]] = defaultdict(set)
        backlinks_graph: Dict[str, Set[str]] = defaultdict(set)
        note_index: Dict[str, str] = {}

        all_files = self.list_notes()
        for file_path in all_files:
            note_stem = file_path.stem
            note_index[note_stem] = str(file_path.relative_to(self.vault))
            forward_graph[note_stem] = set()

        for file_path in all_files:
            source_note = file_path.stem
            parsed = self.parse_note(file_path)
            for target in parsed["links"]:
                target_clean = target.strip()
                if not target_clean:
                    continue
                forward_graph[source_note].add(target_clean)
                backlinks_graph[target_clean].add(source_note)

        self.forward_graph = {k: sorted(list(v)) for k, v in forward_graph.items()}
        self.backlinks_graph = {k: sorted(list(v)) for k, v in backlinks_graph.items()}
        self.note_index = note_index

        return {
            "total_notes": len(all_files),
            "forward_graph": self.forward_graph,
            "backlinks_graph": self.backlinks_graph,
        }

    def find_outgoing_links(self, note_name: str) -> List[str]:
        clean_name = Path(note_name).stem
        if not hasattr(self, "forward_graph"):
            self.build_graph()
        return self.forward_graph.get(clean_name, [])

    def find_backlinks(self, note_name: str) -> List[str]:
        clean_name = Path(note_name).stem
        if not hasattr(self, "backlinks_graph"):
            self.build_graph()
        return self.backlinks_graph.get(clean_name, [])

    def find_related_notes(self, note_name: str) -> List[str]:
        clean_name = Path(note_name).stem
        outgoing = set(self.find_outgoing_links(clean_name))
        incoming = set(self.find_backlinks(clean_name))
        related = (outgoing | incoming) - {clean_name}
        return sorted(list(related))