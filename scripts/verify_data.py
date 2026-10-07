from pathlib import Path
import hashlib
path=Path(__file__).resolve().parents[1]/'data/telco.csv'
expected='16320c9c1ec72448db59aa0a26a0b95401046bef5d02fd3aeb906448e3055e91'
assert hashlib.sha256(path.read_bytes()).hexdigest()==expected, 'Dataset changed; review provenance and retrain explicitly'
print('Dataset checksum verified')
