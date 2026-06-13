# Image processor (HTTP Cloud Function)

Synchronous image pipeline for AED Locator:

1. Download object from the temp (inbox) bucket
2. Verify bytes are a real image and match allowed types/size
3. Resize, normalize, and convert to WebP
4. Upload to the final images bucket
5. Return `{ "success": true, "final_object_key": "..." }` or `{ "success": false, "error": "..." }`

Deploy as an **HTTP-triggered** function (not GCS event triggers). Set `IMAGE_PROCESSOR_URL` on the API to the function URL.

Local run:

```bash
cd functions/image_processor
pip install -r requirements.txt
python main.py
```

Then set `IMAGE_PROCESSOR_URL=http://localhost:8081/` in the API `.env`.
