# How to Make Viral Motion Graphics With AI With 0$ (Turned it into a Skill)

- **Channel:** Jad M.H  | AI Automation
- **URL:** https://www.youtube.com/watch?v=zke3bTtvmLo
- **Category:** AI Systems
- **Processed:** 2026-10-09

## Summary
By combining LLM text generation with local code execution, browser screenshot automation, and FFmpeg, you can generate complete, zero-cost motion graphics and lyric videos from a single prompt.

## Key Takeaways
- LLMs like Claude cannot directly output video files (MP4), but they can generate HTML/CSS code that represents every frame, which can be captured via browser automation and stitched together using FFmpeg.
- A successful AI video prompt requires structured context, a detailed story, explicit negative constraints to avoid default aesthetics, and a robust workflow or framework (like HyperFrames).
- Local open-source models such as ACE-Step 1.5 for music and Kokoro-82M for voiceovers allow you to build complete video production pipelines entirely for free on a standard laptop.
- The 10/90 rule applies to AI video generation: 10% is the prompt and the other 90% is the setup, framework constraints, and critique loops around it.
- Implementing a critique loop where the model evaluates screenshots of its own output, scores them, and iteratively fixes the worst problems drastically improves final video quality.

## Actionable Frameworks
### The Critique Loop Workflow
A methodology where the AI renders a contact sheet of key frame screenshots, scores them across multiple parameters (story, composition, typography, sync), identifies the worst problems, fixes them, and repeats until all shots reach a target score.

### Negative Constraint Prompting
Explicitly listing prohibited defaults, colors, fonts, and styles in your prompt to prevent the AI from falling back onto generic, overused templates.

## Memorable Quotes
> The prompt is 10% of the video. The other 90% is the setup around it.

> Sound is what starts to feel like a real video.

> Without a reference, opus falls back to its default look: centered text, gradient background, everything fading in.

## Tags
`#ai` `#automation` `#generative-ai` `#programming` `#workflow`
