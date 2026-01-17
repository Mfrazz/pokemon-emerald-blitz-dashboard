import shutil
import subprocess
from pathlib import Path

# --------------------
# Config
# --------------------
# Path to your submodule
SUBMODULE_PATH = Path("pokemon-assets/assets")

# Path where you want the assets copied in your main repo
TARGET_PATH = Path("assets")

# --------------------
# Step 1: Update submodule
# --------------------
print("Updating submodule...")
subprocess.run(["git", "submodule", "update", "--remote"], check=True)

# --------------------
# Step 2: Copy updated assets
# --------------------
if TARGET_PATH.exists():
    print(f"Removing existing assets folder: {TARGET_PATH}")
    shutil.rmtree(TARGET_PATH)

print(f"Copying new assets from {SUBMODULE_PATH} to {TARGET_PATH}")
shutil.copytree(SUBMODULE_PATH, TARGET_PATH)

print("Assets updated successfully!")
print("You can now git add and commit the updated assets folder.")