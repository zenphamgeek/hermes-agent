# Thumbnail Prompt Template

## Hướng dẫn sinh prompt cho image_generation_tool

Khi tạo thumbnail, sinh prompt theo cấu trúc sau:

### Template chuẩn

```
A modern tech YouTube thumbnail, vibrant dark background with neon gradients (purple, cyan, blue),
[MAIN VISUAL ELEMENT based on topic],
clean minimalist design, professional tech aesthetic,
high contrast, dramatic lighting, 3D elements,
no text overlay (text will be added by make_thumbnail.py),
16:9 aspect ratio, ultra high quality, 4K
```

### Ví dụ prompt theo chủ đề

**AI Agents:**
```
A modern tech YouTube thumbnail, vibrant dark background with neon purple and cyan gradients,
a futuristic AI robot face made of glowing circuit lines and neural network patterns,
floating holographic data streams around it,
clean minimalist design, professional tech aesthetic,
high contrast, dramatic lighting, 3D depth effect,
no text overlay, 16:9 aspect ratio, ultra high quality
```

**Vibe Coding:**
```
A modern tech YouTube thumbnail, deep dark blue background with electric green accents,
a split screen showing a human hand typing and an AI hand coding simultaneously,
code fragments floating in neon light, futuristic IDE interface,
clean minimalist design, professional tech aesthetic,
no text overlay, 16:9 aspect ratio, ultra high quality
```

**Local LLM:**
```
A modern tech YouTube thumbnail, dark gradient from deep purple to midnight blue,
a powerful workstation GPU glowing with neural network patterns,
small AI brain hologram floating above it, server rack aesthetic,
clean minimalist design, dramatic lighting,
no text overlay, 16:9 aspect ratio, ultra high quality
```

## Quy tắc
1. **Không bao gồm text** trong prompt AI — text sẽ được overlay bởi `make_thumbnail.py`
2. **Luôn dùng dark background** — thumbnail sáng quá sẽ bị mất trên feed
3. **Ít nhất 1 focal point** rõ ràng — viewer phải hiểu chủ đề trong 1 giây
4. **Dùng neon/gradient** — tạo cảm giác tech, hiện đại
5. **16:9** cho YouTube, sẽ crop sang các tỷ lệ khác bằng script
