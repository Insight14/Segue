import json
import sys
from pathlib import Path

# Add src to sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir / "src"))

from api.main import app  # noqa: E402


def export_openapi() -> None:
    openapi_schema = app.openapi()
    output_path = root_dir / "openapi.json"
    output_path.write_text(json.dumps(openapi_schema, indent=2))
    print(f"Exported OpenAPI schema to {output_path}")

    # Also export copy to mobile app
    mobile_openapi_path = root_dir.parent.parent / "apps" / "mobile" / "openapi.json"
    mobile_openapi_path.parent.mkdir(parents=True, exist_ok=True)
    mobile_openapi_path.write_text(json.dumps(openapi_schema, indent=2))
    print(f"Exported OpenAPI schema to {mobile_openapi_path}")


if __name__ == "__main__":
    export_openapi()
