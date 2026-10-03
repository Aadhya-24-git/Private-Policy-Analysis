# Models Directory

This directory is designated for local LLM weights, GGUF quantized models (e.g. Qwen2.5-7B-Instruct), and local embedding weights (e.g. HuggingFace / sentence-transformers).

### Modular Architecture:
- Online AI services (OpenAI / Anthropic) can be swapped seamlessly for offline / local models stored here or served via Ollama.
- Large binary weights (*.bin, *.gguf, *.onnx) are ignored in version control via `.gitignore`.
