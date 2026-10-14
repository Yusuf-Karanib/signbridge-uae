# SignBridge UAE

Public repository: [github.com/Yusuf-Karanib/signbridge-uae](https://github.com/Yusuf-Karanib/signbridge-uae)

SignBridge is a local webcam prototype configured for **8 candidate isolated signs** plus a confirmation-first reception workflow:

- 4 American Sign Language signs with English text and speech.
- 4 Emirati Sign Language signs with Arabic text and speech.

It is designed to recognize one prompted sign at a time after local training. The current saved ASL model is personalized and unvalidated, and no Emirati model exists yet. The **SignBridge agent** turns a confirmed sign into one clear reception-desk request, runs a matching safe local action, remembers staff replies between turns, and clears the temporary session when finished. It is not a full sign-language translator.

For a complete beginner-friendly explanation of the idea, design, screens, training,
testing, files and event demonstration, read `docs/FULL_BEGINNER_GUIDE.md`.
For the exact camera, slide, volume and mouse controls in the current version,
read `docs/CONTROL_GUIDE.md`.
For the bounded championship scope and demonstration, read
`docs/COMPETITION_GUIDE.md`.

## Start it

1. Run `setup.ps1` once. PowerShell is needed only for this setup step.
2. Double-click `Start SignBridge.vbs`. It opens the app without a terminal window.
3. Open **Train model**.
4. Choose a language and enter a short Person ID.
5. Confirm the person's consent, then record 20 to 30 varied examples per class from the demonstrator, or use **Import short video** for a consented 2–5 second clip containing exactly one selected sign. For unseen-person testing, use several training people and keep different people for Final test.
6. Press **Train or update this language model**.
7. Open **SignBridge agent** and record one sign.
8. Confirm the camera suggestion, choose the exact request, and confirm the full sentence.
9. Open **Staff desk** to accept the saved task, type a reply and complete it. You can optionally connect a tested HTTPS Slack/Teams-compatible webhook.
10. Use **Final test** with people who were never used for training.
11. For a focused presentation, press **Competition demo**. It shows only the visitor agent and Staff desk and permits only `Help` followed by directions, appointment help or an interpreter request.

The camera panel shows live FPS. If the default webcam is wrong or busy, choose
camera 1 or 2 and press **Restart**; saved samples and models are unaffected.

If the normal launcher does not open the window, run `diagnose_signbridge.bat`.
That troubleshooting launcher deliberately keeps a terminal visible. Unexpected
startup errors are also written to `outputs/startup.log`.

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
7. The SignBridge agent requires confirmation of both the sign and the complete request before speech or action.
8. A small rule-based action engine creates persistent local reception tasks and can use an earlier staff reply during the same session.
9. The Staff desk records successful, wrong-action and cancelled outcomes. An optional webhook can notify a real staff channel only after it is explicitly configured and enabled.
10. Ending the signer session clears temporary conversation text. The staff task remains until staff records its real outcome.
11. A privacy-safe evidence report measures task completion, false actions, corrections and staff completion time without exporting replies or participant IDs.

Speech is manual by default so a wrong result is not spoken automatically. Automatic speech can be enabled for a controlled demo.

Only landmark coordinates are stored by the training screen. Explicit consent confirmation is required and recorded with new samples. Imported videos are read once and are not copied into SignBridge.
Participant records can be permanently deleted by Person ID. Because one model may mix several people's samples, deleting any participant also removes every trained model and requires retraining.

## Configured candidate vocabulary

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
- The agent supports a short conversation made from predefined, confirmed requests.
- Local task IDs persist on this computer. They do not change a booking or request an interpreter. A staff notification is external only when you deliberately configure and enable a webhook.
- Facial grammar is not classified in this version.
- Source entries are linked, but recorded performances remain unverified until fluent signers and target users review them.
- The shared ZIP contains no personal samples or trained model. It must be set up and trained before camera recognition works on another computer.
- Confidence is a model score, not proof.
- Not suitable for emergencies, medical decisions or replacing interpreters.
- Arabic speech requires an Arabic Windows voice to be installed.

