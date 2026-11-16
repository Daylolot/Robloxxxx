"""v40 = v39 (this folder's build_place.py) + the blood wave-front layer of the neighbouring session (sources/blood-front).
Usage (repo root, repo venv):  python sources/evolution-v39/build_v40.py <output.rbxl> [--qa] [--perf]
Default is the QUALITY build (nothing is cut for phones or weak PCs); --perf adds the performance profile.
Step 1 builds v39 into a temporary file, step 2 applies sources/blood-front/build_place.py on it (it replaces only the
ReplicatedStorage modules BloodLiquidMath and BloodLiquidSurface and checks the v38 liquid is what it expects)."""
import subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "maps" / "Kontur_Office_v26_Mirror.rbxl"
if len(sys.argv) < 2 or sys.argv[1].startswith("--"):
    sys.exit("usage: build_v40.py <output.rbxl> [--qa] [--perf]")
output = Path(sys.argv[1])
assert output.resolve() != BASE.resolve(), "output must not be the base map"
assert set(sys.argv[2:]) <= {"--qa", "--perf"}, "unknown option"
qa = [o for o in ("--qa", "--perf") if o in sys.argv[2:]]
with tempfile.TemporaryDirectory() as temp:
    middle = Path(temp) / "v39.rbxl"
    subprocess.run([sys.executable, str(ROOT / "sources/evolution-v39/build_place.py"), str(BASE), str(middle), *qa], check=True, cwd=ROOT)
    subprocess.run([sys.executable, str(ROOT / "sources/blood-front/build_place.py"), str(middle), str(output)], check=True, cwd=ROOT)
print("built", output)
