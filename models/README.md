# EduGenie Local Models Directory

This folder is dedicated to local machine learning models used by EduGenie.

## Default Local Model: `MBZUAI/LaMini-Flan-T5-783M`

EduGenie integrates the **LaMini-Flan-T5-783M** lightweight sequence-to-sequence model for offline concept explanations.

### Architecture Highlights
- **Base Architecture**: Flan-T5 (Encoder-Decoder Transformer)
- **Parameter Count**: 783 Million Parameters
- **Trained By**: MBZUAI (instruction-tuned for clear, concise responses)
- **Primary Task**: Concept explanations for students

### Automatic Lazy Loading & Fallback
1. **Lazy Loading**: The model is NOT loaded during server boot to keep startup instantaneous. It is downloaded and initialized only on the first concept explanation request.
2. **Memory Caching**: Once loaded into RAM/VRAM, the pipeline is cached in memory for fast sub-second inference on subsequent queries.
3. **Automatic Fallback**: If PyTorch, Transformers, or GPU/CPU memory is insufficient, EduGenie automatically falls back to Google Gemini without throwing an unhandled exception or interrupting user experience.

### Disabling Local Model
If you wish to use Google Gemini exclusively for all explanations, set:
```env
USE_LOCAL_MODEL=False
```
in your `.env` file.
