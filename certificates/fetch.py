"""Download a File Manager artifact by signed URL and strip any signed URLs from JSON content.

Signed URLs are short-lived bearer links; they are removed before anything is published.
"""
import json, re, sys, urllib.request

def scrub(o):
    if isinstance(o, dict):
        return {k: scrub(v) for k, v in o.items() if k != "signed_url"}
    if isinstance(o, list):
        return [scrub(v) for v in o]
    if isinstance(o, str) and "X-Goog-Signature" in o:
        return re.sub(r"\?X-Goog-[^\s\"']*", "?<signed-query-removed>", o)
    return o

url, dest = sys.argv[1], sys.argv[2]
data = urllib.request.urlopen(url, timeout=60).read()
try:
    obj = json.loads(data.decode("utf-8"))
    obj = scrub(obj)
    open(dest, "w", encoding="utf-8").write(json.dumps(obj, indent=1, ensure_ascii=False))
    kind = "json (scrubbed)"
except Exception:
    open(dest, "wb").write(data)
    kind = "binary"
print(dest, len(data), "bytes", kind)
