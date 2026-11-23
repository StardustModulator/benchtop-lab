---
name: lesson-writing
description: Style guide and structure for Benchtop Lab lessons, rubrics and starter code. Use when writing anything under projects/ or docs/ concepts and guides.
---

# Writing Benchtop Lab lessons

## Page structure (every project README / lesson index)
1. Title and one-sentence promise ("By the end you will …").
2. Box: time, compute (CPU/GPU), prerequisites, what you hand in.
3. Learning objectives (3–5, measurable verbs: implement, measure, diagnose, explain).
4. Concepts, each followed by a short runnable step.
5. Predict → Run → Explain blocks (`!!! question "Predict"` admonitions) before key experiments.
6. Deliverables and the rubric table (Pass / Merit / Distinction with exact thresholds and how they are measured).
7. Common failures (symptom → cause → fix), from real failure galleries.
8. Further reading (HF Robotics Course, LeRobot docs, papers) with links.

## Voice
- Second person, plain English, short sentences. Define each term on first use. No hype.
- Show exact commands that were actually run, and their real output (trimmed). Numbers must come from recorded results
  or be marked *provisional*.
- Prefer diagrams (mermaid) and small plots over long prose. Every image has alt text.

## Starter code
- TODOs are small and ordered, each with a hint and a test that checks behaviour, not implementation details.
- The solution lives in `solution/`; starter tests must not import it.

## Licensing
- Lesson text and figures: CC BY 4.0 (footer handles it). Code blocks and files: Apache-2.0 with SPDX headers.
