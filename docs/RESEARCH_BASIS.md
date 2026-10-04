# Research basis and dataset decision

Checked on 28 September 2026.

## What this build uses

- **MediaPipe Gesture Recognizer and Holistic Landmarker:** the first model keeps a responsive two-hand preview and supplies safe generic control gestures. Holistic adds both hands and upper-body position only while a sign is being recorded. The recorded sequence can learn movement instead of treating every sign as one still image.
- **A separate classifier for each language:** ASL and Emirati Sign Language never share a label or assume the same movement.
- **Local, consented examples:** only landmark coordinates are saved. The app does not save webcam video.
- **Unknown examples and confidence rejection:** unsupported or unclear attempts should produce no text or sound.

This keeps the useful collect-train-demonstrate flow from Nicholas Renotte's TensorFlow Object Detection video, but replaces per-frame object boxes with current hand/body landmarks and motion over time. The separate computer-control mode uses Google's published generic gesture model; those shortcuts are not presented as ASL or Emirati signs.

## Sources reviewed

| Source | What it contains | Licence or access point | Decision |
| --- | --- | --- | --- |
| [MediaPipe Holistic](https://ai.google.dev/edge/api/mediapipe/python/mp/tasks/vision/HolisticLandmarker) | Hand, pose and face landmarks for images/video | Google MediaPipe distribution | Used for local landmark extraction |
| [ASL Citizen](https://www.microsoft.com/en-us/research/project/asl-citizen/) | About 84,000 isolated-sign videos, 2,700 ASL signs, varied signers | Research licence; contact Microsoft for commercial use | Strong evidence for isolated-sign and unseen-signer testing; dataset not bundled |
| [PopSign ASL](https://signdata.cc.gatech.edu/view/datasets/popsign_v1_0/) | More than 210,000 examples of 250 isolated ASL signs from consenting Deaf signers | CC BY 4.0 | Useful future ASL training source; phone-oriented one-handed adaptations still require form review |
| [ASL Signbank](https://aslsignbank.com/) | Curated ASL sign entries and variants | CC BY-NC-SA 4.0 | Exact ASL source links; media not copied |
| [WLASL](https://github.com/dxli94/WLASL) | 2,000 isolated ASL word classes | C-UDA; non-commercial computational use | Useful benchmark; not bundled |
| [How2Sign](https://how2sign.github.io/) | More than 80 hours of continuous ASL | CC BY-NC 4.0; research use | Long-term sentence research, not this event build |
| [YouTube-ASL](https://proceedings.neurips.cc/paper_files/paper/2023/hash/5c61452daca5f0c260e683b317d13a3f-Abstract-Datasets_and_Benchmarks.html) | About 984 hours of continuous ASL with English captions | Video IDs and research resources; underlying videos remain third-party content | Evidence for long-term pretraining, not a shortcut to reliable sentence translation |
| [UAE Sign Language Dictionary](https://za.gov.ae/Sign-Language-Dictionary/UAE-Sign-Language-Categories) | Official Emirati sign reference videos | No open training-data licence assumed | Exact links for all four Emirati signs; media not copied |
| [ESL127](https://research.uaeu.ac.ae/en/publications/esl127-emirate-sign-language-datasets-and-e-dictionary-version-20/) | 127 Emirati signs, 50 sentences and 708 recordings from four Deaf Emirati signers | No public download or reusable licence confirmed | Closest Emirati dataset; contact the UAEU authors before any use |
| [Asma'ak](https://zuscholars.zu.ac.ae/works/6327/) | Ten Emirati signs recognized with MediaPipe Holistic and an LSTM on an ordinary laptop | Published system description; its dataset is not treated as reusable | Direct evidence that the event-scale webcam approach is technically reasonable |
| [KArSL-502](https://hamzah-luqman.github.io/KArSL/download_video_502.html) | 502 isolated Arabic sign words, 75,300 Kinect samples, 3 professional signers | Downloads are available; no broad reuse licence confirmed | Useful ArSL benchmark, but not proof of Emirati variants |
| [ArabSign](https://hamzah-luqman.github.io/ArabSign/) | 9,335 continuous sentence samples, 50 sentences, 6 signers | Request access from the author | Long-term ArSL sentence research, not this event build |

## Why public datasets are not copied into version one

- Several datasets restrict commercial use or require permission.
- ASL data cannot validate Emirati signs.
- General Arabic Sign Language data cannot automatically validate a UAE regional form.
- Large video models need more data and computing time than this event deadline allows.

The honest first target is 8 isolated, prompted signs. Continuous conversation translation remains a later research project.

MediaPipe can also return face landmarks, but this version does not classify facial grammar. A future sentence system must model facial and other non-manual information rather than simply joining isolated sign guesses.

## What the latest check changed

- The older object-detection tutorial remains useful as a demonstration workflow, not as the design to copy.
- Published Emirati work already uses MediaPipe landmarks and motion models, so this project is not claiming a new scientific invention.
- A 2024 Arabic landmark study reported a large drop between familiar-signer and unseen-signer accuracy. SignBridge therefore keeps people separate during final evaluation.
- More model complexity will not replace varied, correctly performed examples.

## Related UAE products and research

- [ChatSign at NYU Abu Dhabi](https://nyuad.nyu.edu/en/news/latest-news/science-and-technology/2026/may/nyuad-launches-chatsign.html) works on ASL and Emirati Sign Language.
- [HearMe at Abu Dhabi University](https://www.mediaoffice.abudhabi/en/education/abu-dhabi-university-secures-patent-for-ai-powered-multilingual-sign-language-translation-application/) works on sign/text translation.
- [Eshara](https://eshara.ai/) works on Arabic sign-language accessibility using digital avatars.

These projects validate the need, but their public claims are not independent benchmarks for SignBridge. SignBridge should be presented as a transparent, testable isolated-sign prototype.
