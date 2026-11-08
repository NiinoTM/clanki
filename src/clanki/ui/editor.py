"""Unix-style external editor integration for card modification."""

import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import tempfile
from typing import Dict, Optional


def get_default_editor() -> str:
    """Determine the system editor from environment or standard CLI fallbacks."""
    editor = os.environ.get("VISUAL") or os.environ.get("EDITOR")
    if editor:
        return editor

    for candidate in ["nano", "nvim", "vim", "vi"]:
        if shutil.which(candidate):
            return candidate

    return "vi"


class CardEditor:
    """Handles writing note fields to a temporary file and parsing edits back."""

    HEADER_TEMPLATE = (
        "# ====================================================================\n"
        "# CLANKI CARD EDITOR\n"
        "# Edit the field values below.\n"
        "# Lines starting with '#' before the first field are ignored.\n"
        "# Save and exit your editor (e.g., Ctrl+O, Ctrl+X in nano, :wq in vim)\n"
        "# to apply your changes to Anki.\n"
        "# ====================================================================\n\n"
    )

    def edit_fields(self, fields: Dict[str, str]) -> Optional[Dict[str, str]]:
        """Open fields in $EDITOR. Returns updated fields or None if unchanged/cancelled."""
        editor_cmd = get_default_editor()

        # Build initial editable buffer
        content = self.HEADER_TEMPLATE
        for field_name, field_val in fields.items():
            content += f"# === FIELD: {field_name} ===\n{field_val}\n\n"

        # Create temporary file
        with tempfile.NamedTemporaryFile("w+", suffix=".txt", delete=False, encoding="utf-8") as tf:
            tf.write(content)
            temp_path = tf.name

        try:
            cmd = shlex.split(editor_cmd) + [temp_path]
            proc = subprocess.run(cmd)
            if proc.returncode != 0:
                return None

            edited_text = Path(temp_path).read_text(encoding="utf-8")
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

        updated_fields = self._parse_fields(edited_text, list(fields.keys()))
        if updated_fields == fields:
            return None  # No modifications made

        return updated_fields

    def _parse_fields(self, text: str, field_names: list[str]) -> Dict[str, str]:
        """Extract field values from the edited buffer demarcated by '# === FIELD: name ==='."""
        field_lines: Dict[str, list[str]] = {name: [] for name in field_names}
        current_field: Optional[str] = None

        for line in text.splitlines():
            field_match = re.match(r"^#\s*===\s*FIELD:\s*(.+?)\s*===$", line)
            if field_match:
                name = field_match.group(1).strip()
                if name in field_lines:
                    current_field = name
                else:
                    current_field = None
                continue

            if current_field is not None:
                field_lines[current_field].append(line)

        return {
            name: "\n".join(lines).strip()
            for name, lines in field_lines.items()
        }