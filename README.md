# SignBridge UAE

SignBridge is a local webcam prototype for **8 isolated signs**:

- 4 American Sign Language signs with English text and speech.
- 4 Emirati Sign Language signs with Arabic text and speech.

It recognizes one prompted sign at a time. It is not a full sign-language translator.

For a complete beginner-friendly explanation of the idea, design, screens, training,
testing, files and event demonstration, read `docs/FULL_BEGINNER_GUIDE.md`.

## Start it

1. Run `setup.ps1` once.
2. Double-click `start_signbridge.bat`.
3. Open **Train model**.
4. Choose a language and enter a short Person ID.
5. For a personalized demo, record 20 to 30 varied examples per class from the demonstrator. For unseen-person testing, use several training people and keep different people for Final test.
6. Press **Train or update this language model**.
7. Open **Recognize** and record one sign.
8. Use **Final test** with people who were never used for training.

The camera panel shows live FPS. If the default webcam is wrong or busy, choose
camera 1 or 2 and press **Restart**; saved samples and models are unaffected.

The **Computer control** tab is a separate experiment. It uses Google's generic
hand gestures to control volume, slides or the mouse. It is not sign-language
recognition. Control is off by default and requires an open-palm safety hold.

## Before a public demonstration

- A fluent ASL signer must check every ASL form.
- A fluent Emirati signer or qualified local interpreter must check every Emirati form.
- Record several people when possible. If only the demonstrator trains it, clearly call the result a personalized proof of concept.
- Aim for at least 85% balanced accuracy on unseen people.
- If a sign performs badly, remove or replace it rather than hiding the result.

The exact checklist is in `docs/TEST_PLAN.md`.

## How it works

1. MediaPipe Gesture Recognizer tracks up to two hands for a steadier preview.
2. During a sign recording, MediaPipe Holistic also finds hand and upper-body points.
3. SignBridge records a 1.8-second sequence of those points.
4. The sequence is resized to 32 time steps and includes movement speed.
5. A separate classifier is trained for each sign language.
6. Low-confidence results are rejected instead of guessed.

Speech is manual by default so a wrong result is not spoken automatically. Automatic speech can be enabled for a controlled demo.

Only landmark coordinates are stored by the training screen. Camera video is not stored.

## Current vocabulary

- ASL: `Hello`, `Help`, `Water`, `Again`.
- Emirati Sign Language: `Drink`, `Help`, `Wait`, `Repeat`.

Each training choice links to its exact source entry. The ASL and Emirati movements are independent. Similar written meanings do not mean the signs are the same.

## Research basis

The project follows the useful demonstration flow in Nicholas Renotte's older TensorFlow Object Detection tutorial, but it does not copy that architecture. It uses current MediaPipe hand and Holistic landmark tracking plus a short motion-sequence classifier. This better represents hand shape, sign location, two-handed movement and motion over time.

Useful references:

- MediaPipe Holistic: https://ai.google.dev/edge/api/mediapipe/python/mp/tasks/vision/HolisticLandmarker
- ASL Citizen: https://www.microsoft.com/en-us/research/project/asl-citizen/
- ASL Signbank: https://aslsignbank.com/
- UAE Sign Language Dictionary: https://za.gov.ae/Sign-Language-Dictionary/UAE-Sign-Language-Categories
- Inspiration video: https://www.youtube.com/watch?v=pDXdlXlaCco

The dataset and licence comparison is in `docs/RESEARCH_BASIS.md`.

## Limitations

- Isolated signs only.
- Facial grammar is not classified in this version.
- Source entries are linked, but recorded performances remain unverified until fluent signers review them.
- Confidence is a model score, not proof.
- Not suitable for emergencies, medical decisions or replacing interpreters.
- Arabic speech requires an Arabic Windows voice to be installed.

