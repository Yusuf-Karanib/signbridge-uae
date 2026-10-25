# SignBridge UAE

Public repository: [github.com/Yusuf-Karanib/signbridge-uae](https://github.com/Yusuf-Karanib/signbridge-uae)

SignBridge is a local webcam prototype currently focused on **4 isolated ASL signs with English text and speech** plus a confirmation-first hotel-service workflow.

The Emirati vocabulary and earlier work remain saved in the repository, but that mode is hidden until the ASL model has been tested and improved using real feedback. It is designed to recognize one prompted sign at a time after local training. The current saved ASL model is personalized and unvalidated. The **SignBridge Access Agent hotel pilot** turns a confirmed sign into one supported hotel request, creates and tracks a safe staff task, shows its progress, asks the guest whether the request was resolved, and clears the temporary session when finished. It is not a full sign-language translator.

For a complete beginner-friendly explanation of the idea, design, screens, training,
testing, files and event demonstration, read `docs/FULL_BEGINNER_GUIDE.md`.
For the exact camera, slide, volume and mouse controls in the current version,
read `docs/CONTROL_GUIDE.md`.
For the bounded championship scope and demonstration, read
`docs/COMPETITION_GUIDE.md`.
For the current startup-programme sequence and application readiness gates, read
`docs/STARTUP_PROGRAMME_ROADMAP.md`.
The latest technical review and exact changes are in `docs/REVIEW_2026_10_25.md`.
After this update, retrain the ASL model once to use the corrected confidence
training. Your existing samples are kept.

## Start it

1. Run `setup.ps1` once. PowerShell is needed only for this setup step.
2. Double-click `Start SignBridge.vbs`. It opens the app without a terminal window.
3. Open **Train model**.
4. ASL is already selected. Enter a short Person ID.
5. Confirm the person's consent, then record 20 to 30 varied examples per class from the demonstrator, or use **Import short video** for a consented 2–5 second clip containing exactly one selected sign. For unseen-person testing, use several training people and keep different people for Final test.
6. Optional: use **Import a PopSign training folder** for original licensed PopSign TRAIN clips. See `docs/ASL_DATASET_IMPORT.md`.
7. Press **Train or update this language model**.
8. Open **SignBridge agent** and record one sign.
9. Confirm the camera suggestion, choose the exact request, and confirm the full sentence.
10. Open **Staff desk** to accept the saved task, type a reply and mark the service delivered. The guest then confirms whether it was resolved. You can optionally connect a tested HTTPS Slack/Teams-compatible webhook.
11. Use **Final test** with people who were never used for training. Confirm testing permission, then record live or choose **Import test video** for one short, untouched clip. Test results never become training data.
12. For a focused presentation, press **Competition demo**. It shows only the guest agent and Staff desk and permits only `Help` followed by hotel check-in assistance, a room/hotel service request or an interpreter request.

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
- Record several people when possible. If only the demonstrator trains it, clearly call the result a personalized proof of concept.
- Aim for at least 85% balanced accuracy on unseen people.
- If a sign performs badly, remove or replace it rather than hiding the result.

The exact checklist is in `docs/TEST_PLAN.md`.

## How it works

1. MediaPipe Gesture Recognizer tracks up to two hands for a steadier preview.
2. During a sign recording, MediaPipe Holistic also finds hand and upper-body points.
3. SignBridge records a 1.8-second sequence of those points.
4. The sequence is resized to 32 time steps and includes movement speed.
5. An ASL classifier is trained from the saved landmark sequences.
6. Low-confidence results are rejected instead of guessed.
7. The SignBridge agent requires confirmation of both the sign and the complete request before speech or action.
8. A small rule-based action engine creates persistent local hotel tasks and can use an earlier staff reply during the same session.
9. The Staff desk records delivery, wrong-action and cancelled outcomes. A request counts as successful only after the guest confirms it was resolved. An optional webhook can notify a real staff channel only after it is explicitly configured and enabled.
10. Ending the signer session clears temporary conversation text. The staff task remains until staff records its real outcome.
11. A privacy-safe evidence report includes rejected camera attempts, manual fallbacks, journeys ending before any task, guest resolution and time from first attempt to final resolution. It does not export replies or participant IDs.

Speech is manual by default so a wrong result is not spoken automatically. Automatic speech can be enabled for a controlled demo.

Only landmark coordinates are stored by the training screen. Explicit consent confirmation is required and recorded with new samples. Imported videos are read once and are not copied into SignBridge.
Participant records can be permanently deleted by Person ID. Because one model may mix several people's samples, deleting any participant also removes every trained model and requires retraining.

## Current candidate vocabulary

- ASL: `Hello`, `Help`, `Water`, `Again`.

PopSign v2.1 contains reusable original training clips for `Hello`, `Help` and `Water`; it does not contain `Again`, so the importer will never substitute a different sign. `Again` and `OTHER / NO SIGN` still need separate, correctly labelled examples. Each training choice links to its exact source entry.

Deferred phase: the saved Emirati candidates are `Drink`, `Help`, `Wait` and `Repeat`. They will return only after the ASL phase receives useful validation feedback.

## Research basis

The project follows the useful demonstration flow in Nicholas Renotte's older TensorFlow Object Detection tutorial, but it does not copy that architecture. It uses current MediaPipe hand and Holistic landmark tracking plus a short motion-sequence classifier. This better represents hand shape, sign location, two-handed movement and motion over time.

Useful references:

- MediaPipe Holistic: https://ai.google.dev/edge/api/mediapipe/python/mp/tasks/vision/HolisticLandmarker
- ASL Citizen: https://www.microsoft.com/en-us/research/project/asl-citizen/
- PopSign ASL v2.1: https://signdata.cc.gatech.edu/view/datasets/popsign_v2_1/index.html
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
- The current active app phase is ASL with English output; Emirati support is deferred, not completed.

