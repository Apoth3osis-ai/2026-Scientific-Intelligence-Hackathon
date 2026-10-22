"""Download a qpcert byte-for-byte and check its SHA-256 against the certificate_sha256 reported by certify_circuit."""
import hashlib, sys, urllib.request
url, dest, expected = sys.argv[1], sys.argv[2], sys.argv[3]
data = urllib.request.urlopen(url, timeout=60).read()
assert b"X-Goog-Signature" not in data, "signed URL inside certificate"
open(dest, "wb").write(data)
got = hashlib.sha256(data).hexdigest()
print(dest, len(data), "bytes", "sha256 OK" if got == expected else f"sha256 MISMATCH {got}")
