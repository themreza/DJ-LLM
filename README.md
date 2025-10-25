# DJ LLM

Fine-tuning multimodal LLMs to be world-class DJs 🎵

![](assets/images/dj-llm-small.png)


## Tasks

- **Song Structure Analysis** — Identify sections like intro, verse, chorus, drop, and outro  
- **BPM Estimation** — Estimate the tempo or rhythmic feel of a track  
- **Key and Chord Detection** — Detect musical key and chord progressions  
- **Genre Classification** — Classify the track into one or more genres  
- **Mood and Energy Analysis** — Tag tracks with emotional and intensity labels
- **Cue Point Recommendation** — Suggest where to start or end playback for mixing  
- **Instrumental and Vocal Presence Detection** — Identify if a track has vocals or is instrumental  
- **Loop Region Suggestion** — Find sections that can be looped smoothly  
- **Drop Detection** — Locate the most impactful or climactic moment  

## Dataset

A novel annotated dataset of music licensed under Creative Commons is introduced. The annotations are provided as metadata for each audio file, containing information such as song sections, BPM, key, chord progression, genre, mood, energy, cue points, instrumental and vocal sections, loopable regions, and beat drops.

## LLMs

The provided dataset can be used to fine-tune any multimodal LLM suitable for audio understanding, capable of simultaneously processing text and audio inputs.

The project is currently based on [Qwen3-Omni](https://github.com/QwenLM/Qwen3-Omni). Support for [more advanced](https://github.com/BradyFU/Awesome-Multimodal-Large-Language-Models) and [smaller multimodal models](https://github.com/stevelaskaridis/awesome-mobile-llm) is planned.

## Inference

The baseline or fine-tuned LLM should be run via Gradio, which provides an API for evaluations and the demo app. This requires a GPU with a sufficiently large VRAM (e.g. Nvidia H100).

Qwen3-Omni has an [official HuggingFace space](https://huggingface.co/spaces/Qwen/Qwen3-Omni-Demo). As an example, the Gradio API address of this space is `https://qwen-qwen3-omni-demo.hf.space/`. However, the model should be run on a local machine with a suitable GPU or via a cloud GPU provider.

Once Gradio is running, inference can be performed using the `inference/infer.py` script:

```
uv run inference/infer.py \
  --client https://qwen-qwen3-omni-demo.hf.space/ \
  --text "Estimate the BPM (beats per minute) of this track. 
  Provide your answer as a single numerical value representing 
  the tempo." \
  --audio ~/Music/Test.mp3
120
```

## Evaluations

### Running

### Results

| Task                                      | Baseline Accuracy | Fine-Tuned Accuracy |
|------------------------------------------|-------------------|---------------------|
| Song Structure Analysis                  |                   |                     |
| BPM Estimation                           |                   |                     |
| Key and Chord Detection                  |                   |                     |
| Genre Classification                     |                   |                     |
| Mood and Energy Analysis                 |                   |                     |
| Cue Point Recommendation                 |                   |                     |
| Instrumental and Vocal Presence Detection|                   |                     |
| Loop Region Suggestion                   |                   |                     |
| Drop Detection                           |                   |                     |

## Demo

## Author

A project by [Mohammad Tomaraei](https://www.linkedin.com/in/tomaraei/)

![](assets/images/mt.png)

## Credits

* [Qwen3-Omni](https://github.com/QwenLM/Qwen3-Omni) is a large language model (LLM) developed by the Qwen team at Alibaba Cloud.

