# Adaptation Notes

The node-ready guides follow these rules:

1. Preserve all prompt-writing knowledge, ordering, examples, constraints, timing, camera, motion, visual, dialogue, sound, and music guidance.
2. Remove only Agent-runtime behavior: tool allowlists and calls, task delegation, canvas operations, interactive confirmation waits, external generation/editing dispatch, project setup, final assembly, and file delivery.
3. When an operational sentence also contains prompt guidance, retain the prompt guidance and remove only the operational clause.
4. Keep required reference files and their original text unless a passage is itself exclusively an Agent-runtime operation.
5. Do not summarize, merge, or shorten retained guidance.

Video optimization combines the complete H3 General guide, the mode-specific official reference guide, and at most one selected scene guide.

Image optimization uses the unmodified released H3-Image-PE T2I or editing task prompt in `h3_image/`. T2I template formatting is resolved before constructing the request. The integration supplies ordered reference evidence and the selected canvas separately, extracts only `expanded_caption`, and never adds video guides. See `h3_image/NOTICE` and `h3_image/LICENSE` for source and licensing.
