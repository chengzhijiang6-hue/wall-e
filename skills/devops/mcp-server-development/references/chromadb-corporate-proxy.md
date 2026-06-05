# ChromaDB in Corporate Proxy / SSL Inspection Environments

## Problem
ChromaDB's default embedding function (`ONNXMiniLM_L6_V2`) downloads an ONNX model archive
from S3 (`https://chroma-onnx-models.s3.amazonaws.com/all-MiniLM-L6-v2/onnx.tar.gz`).
In corporate networks with SSL-inspecting proxies, this fails with:
```
httpx.ConnectError: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed
```

The S3 URL may also return 403 when routed through certain proxies.

## Solution: Pre-download model during Docker build

ChromaDB caches the model at `~/.cache/chroma/onnx_models/all-MiniLM-L6-v2/onnx/`.
The archive contains 6 files (ALL required):
```
config.json
model.onnx
special_tokens_map.json
tokenizer_config.json
tokenizer.json
vocab.txt
```

### download_model.py (build-time script)

```python
import os, httpx, tarfile

MODEL_URL = "https://chroma-onnx-models.s3.amazonaws.com/all-MiniLM-L6-v2/onnx.tar.gz"
DEST_DIR = "/home/appuser/.cache/chroma/onnx_models/all-MiniLM-L6-v2"
ARCHIVE = os.path.join(DEST_DIR, "onnx.tar.gz")

def main():
    os.makedirs(DEST_DIR, exist_ok=True)
    extracted = os.path.join(DEST_DIR, "onnx", "model.onnx")
    if os.path.exists(extracted) and os.path.getsize(extracted) > 10_000_000:
        print("Model already cached"); return

    proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY")
    with httpx.stream("GET", MODEL_URL, proxy=proxy, verify=False,
                       timeout=300, follow_redirects=True) as r:
        r.raise_for_status()
        with open(ARCHIVE, "wb") as f:
            for chunk in r.iter_bytes(65536):
                f.write(chunk)

    with tarfile.open(ARCHIVE, "r:gz") as tar:
        tar.extractall(path=DEST_DIR)
    os.remove(ARCHIVE)
    print("Done")

if __name__ == "__main__":
    main()
```

### Dockerfile snippet

```dockerfile
ARG HTTP_PROXY
ARG HTTPS_PROXY
ENV PYTHONHTTPSVERIFY=0
ENV CURL_CA_BUNDLE=""
ENV REQUESTS_CA_BUNDLE=""

# Pre-download during build
COPY scripts/download_model.py /tmp/download_model.py
RUN python /tmp/download_model.py && rm /tmp/download_model.py

# Create user AFTER download (cache goes to /home/<user>/.cache/)
RUN useradd -m -u 1000 appuser
```

### Key points
- `verify=False` is required due to SSL inspection
- `follow_redirects=True` is required (S3/HuggingFace redirect)
- Download must happen BEFORE creating the runtime user, so the cache lands in the right home dir
- The `PYTHONHTTPSVERIFY=0` env var doesn't help httpx; you must pass `verify=False` explicitly
- ChromaDB checks for ALL 6 files; just `model.onnx` alone is not sufficient
- If S3 is blocked, try HuggingFace mirror but note HF also redirects (302)
