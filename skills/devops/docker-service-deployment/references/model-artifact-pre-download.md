# Pre-Downloading Model Artifacts During Docker Build

When a container needs ML model files (ONNX, sentence-transformers, etc.), 
runtime downloads often fail in corporate proxy environments due to:
- S3/GCS URLs blocked by proxy (403 Forbidden)
- SSL certificate verification failure (proxy SSL inspection rewrites certs)
- Hugging Face redirects blocked by proxy

## Pattern: Pre-download During Build

### Step 1: Create a download script

```python
# scripts/download_model.py
import os, httpx, tarfile

MODEL_URL = "https://example.com/model.tar.gz"
DEST_DIR = "/home/appuser/.cache/models/my-model"
ARCHIVE = os.path.join(DEST_DIR, "model.tar.gz")

def main():
    os.makedirs(DEST_DIR, exist_ok=True)
    if os.path.exists(os.path.join(DEST_DIR, "model.onnx")):
        print("Model already exists")
        return

    proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY")
    # verify=False needed for corporate proxy SSL inspection
    # follow_redirects=True needed for CDN redirects (HuggingFace, S3)
    with httpx.stream("GET", MODEL_URL, proxy=proxy, verify=False, 
                       timeout=300, follow_redirects=True) as r:
        r.raise_for_status()
        with open(ARCHIVE, "wb") as f:
            for chunk in r.iter_bytes(chunk_size=65536):
                f.write(chunk)

    with tarfile.open(ARCHIVE, "r:gz") as tar:
        tar.extractall(path=DEST_DIR)
    os.remove(ARCHIVE)
    print("Done")

if __name__ == "__main__":
    main()
```

### Step 2: Dockerfile

```dockerfile
ARG HTTP_PROXY
ARG HTTPS_PROXY

# Disable SSL verification for build-time downloads
ENV PYTHONHTTPSVERIFY=0

# Copy and run download script
COPY scripts/download_model.py /tmp/download_model.py
RUN python /tmp/download_model.py && rm /tmp/download_model.py

# Switch to non-root user AFTER download (cache dir ownership)
RUN chown -R appuser:appuser /home/appuser/.cache/
USER appuser
```

### Step 3: docker-compose.yml

```yaml
services:
  myservice:
    build:
      context: .
      args:
        HTTP_PROXY: http://proxy:port
        HTTPS_PROXY: http://proxy:port
```

## ChromaDB Specific: ONNX MiniLM L6 v2

ChromaDB's default embedding function downloads `onnx.tar.gz` from:
`https://chroma-onnx-models.s3.amazonaws.com/all-MiniLM-L6-v2/onnx.tar.gz`

The archive extracts to `~/.cache/chroma/onnx_models/all-MiniLM-L6-v2/onnx/` containing:
- model.onnx
- config.json, tokenizer.json, tokenizer_config.json
- special_tokens_map.json, vocab.txt

**All 6 files must be present** — ChromaDB checks for each one.

**S3 URL often blocked** — Use the download pattern above with `verify=False` and `follow_redirects=True`.

## Pitfalls

1. **Download as root, run as user**: Model cache must be owned by the runtime user. Download during build (root), then `chown` before `USER` switch.

2. **SHA256 verification**: Some libraries verify model hashes. If you download from a different source (e.g., HuggingFace mirror instead of S3), the hash may differ. Check if the library does hash verification and handle accordingly.

3. **Incomplete archives**: If the download is interrupted, the extracted files may be partial. Always check file size (>10MB for embedding models) or add size validation in the download script.

4. **Don't delete download scripts mid-project**: The download script (`scripts/download_model.py`) is referenced by the Dockerfile's `COPY` + `RUN` steps. Deleting it during cleanup between builds causes `failed to calculate checksum` or `not found` errors. Keep the script in the repo for the project's lifetime, or remove the Dockerfile COPY+RUN lines at the same time.
