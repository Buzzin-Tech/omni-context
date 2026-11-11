"""UI and Styling Pattern Extractor."""
import re
from typing import Optional, Dict, Any

UI_EXTENSIONS = {".tsx", ".jsx", ".vue", ".svelte", ".html", ".css", ".blade.php"}

TAILWIND_KEYWORDS = [
    r"\bbg-[a-z0-9\/-]+",
    r"\btext-[a-z0-9\/-]+",
    r"\bborder-[a-z0-9\/-]+",
    r"\brounded-[a-z0-9]+",
    r"\bshadow-[a-z0-9]+",
    r"\b(flex|grid|flex-col|items-center|justify-between)\b",
    r"\b(transition|duration-[0-9]+|hover:[a-z0-9\/-]+)",
]

def is_ui_file(file_path: str) -> bool:
    lower = file_path.lower()
    return any(lower.endswith(ext) for ext in UI_EXTENSIONS)

def extract_ui_features(file_path: str, content: str) -> Optional[Dict[str, Any]]:
    if not is_ui_file(file_path) and "className=" not in content and "class=" not in content:
        return None
    
    # Extract tailwind tokens
    tailwind_matches = set()
    for pattern in TAILWIND_KEYWORDS:
        found = re.findall(pattern, content)
        for f in found:
            if isinstance(f, tuple):
                tailwind_matches.update(f)
            else:
                tailwind_matches.add(f)
                
    if len(tailwind_matches) < 4:
        return None  # Not enough styling to be a distinct UI pattern

    # Determine component name
    filename = file_path.replace("\\", "/").split("/")[-1]
    comp_name = filename.split(".")[0]
    
    # Infer tech stack
    tech_stack = "custom-ui"
    if file_path.endswith((".tsx", ".jsx")):
        tech_stack = "react-tailwind" if len(tailwind_matches) > 5 else "react"
    elif file_path.endswith(".vue"):
        tech_stack = "vue"
    elif file_path.endswith(".blade.php"):
        tech_stack = "blade-tailwind"
    elif file_path.endswith(".html"):
        tech_stack = "html-tailwind"

    # Summarize key styling traits
    colors = [m for m in tailwind_matches if m.startswith(("bg-", "text-", "border-"))]
    layout = [m for m in tailwind_matches if m in {"flex", "grid", "flex-col", "items-center", "justify-between"}]
    accents = [m for m in tailwind_matches if m.startswith(("rounded-", "shadow-", "hover:", "transition"))]

    summary_parts = []
    if colors:
        summary_parts.append(f"Palette: {', '.join(sorted(colors)[:6])}")
    if layout:
        summary_parts.append(f"Layout: {', '.join(sorted(layout))}")
    if accents:
        summary_parts.append(f"Accents: {', '.join(sorted(accents)[:5])}")

    style_summary = " | ".join(summary_parts) if summary_parts else "Modern clean UI pattern"

    # Truncate snippet to 2500 chars to save space while capturing full component layout
    snippet = content[:2500] if len(content) > 2500 else content

    return {
        "component_name": comp_name,
        "tech_stack": tech_stack,
        "style_summary": style_summary,
        "code_snippet": snippet
    }
