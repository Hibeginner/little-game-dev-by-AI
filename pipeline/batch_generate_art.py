import json
import sys
import os
from datetime import datetime

sys.path.insert(0, ".")
from art.tools.free_image_generator import PollinationsImageGenerator

# Timestamp for filenames
TIMESTAMP = "20260417_211601"

# Style suffix for consistency
STYLE_SUFFIX = "flat cartoon style, soft warm pastel colors, rounded lines, parent-child theme, high quality, clean lines, consistent style, chibi kawaii aesthetic"

# Answers mapping (question_id -> asset adjustments)
ANSWERS = {
    "q1": {"id": "ui_logo"},
    "q2": {"id": "all_buttons"},
    "q3": {"id": "ui_alertness_bar_bg"},
    "q5": {"id": "ui_bed", "category": "scene"},
    "q6": {"id": "bg_room_normal"},
    "q7": {"id": "all_effects"},
}

# Read requirements
with open(
    "pipeline/outputs/design/art_requirements/art_requirements_20260417_210818.json",
    "r",
    encoding="utf-8",
) as f:
    requirements = json.load(f)

# Read answers
with open(
    "pipeline/outputs/design/art_answers/art_answers_20260417_211449.json",
    "r",
    encoding="utf-8",
) as f:
    answers_data = json.load(f)

# Build updated prompt hints from answers
updated_prompts = {}
for a in answers_data["answers"]:
    if a["question_id"] == "q1":
        updated_prompts["ui_logo"] = a["updated_prompt_hint"]
    elif a["question_id"] == "q2":
        # Apply to all button-type ui assets
        for asset in requirements["assets"]:
            if asset["id"].startswith("ui_btn_"):
                updated_prompts[asset["id"]] = a["updated_prompt_hint"]
    elif a["question_id"] == "q3":
        updated_prompts["ui_alertness_bar_bg"] = a["updated_prompt_hint"]
    elif a["question_id"] == "q6":
        updated_prompts["bg_room_normal"] = a["updated_prompt_hint"]

gen = PollinationsImageGenerator()

results = []
assets = requirements["assets"]

for i, asset in enumerate(assets):
    asset_id = asset["id"]
    category = "scene" if asset_id == "ui_bed" else asset["category"]
    w, h = asset["size"].split("x")

    # Get optimized prompt
    base_prompt = updated_prompts.get(asset_id, asset["prompt_hint"])
    full_prompt = base_prompt + ", " + STYLE_SUFFIX

    # Ensure output directory exists
    output_dir = f"pipeline/outputs/art/assets/{category}"
    os.makedirs(output_dir, exist_ok=True)

    save_path = f"{output_dir}/{asset_id}_{TIMESTAMP}.png"

    print(f"\n[{i + 1}/{len(assets)}] Generating: {asset_id} ({asset['size']})")
    print(f"  Prompt: {full_prompt[:100]}...")

    result = gen.generate(
        prompt=full_prompt, width=int(w), height=int(h), save_path=save_path
    )

    results.append(
        {
            "id": asset_id,
            "file_path": save_path,
            "prompt_used": full_prompt,
            "size": asset["size"],
            "status": "success" if result else "failed",
        }
    )

# Build manifest
manifest = {
    "generated_at": datetime.now().isoformat(),
    "assets": results,
    "summary": {
        "total": len(results),
        "success": sum(1 for r in results if r["status"] == "success"),
        "failed": sum(1 for r in results if r["status"] == "failed"),
    },
}

# Write manifest
manifest_dir = "pipeline/outputs/art/manifest"
os.makedirs(manifest_dir, exist_ok=True)
manifest_path = f"{manifest_dir}/art_manifest_{TIMESTAMP}.json"

with open(manifest_path, "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=2, ensure_ascii=False)

print(f"\n{'=' * 50}")
print(f"Generation complete!")
print(
    f"Total: {manifest['summary']['total']}, Success: {manifest['summary']['success']}, Failed: {manifest['summary']['failed']}"
)
print(f"Manifest saved to: {manifest_path}")
