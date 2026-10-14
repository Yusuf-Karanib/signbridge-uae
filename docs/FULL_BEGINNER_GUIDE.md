# SignBridge UAE: complete beginner guide

This guide explains what SignBridge is, why it was designed this way, how every part works, how to train and test it properly, and how to describe it honestly.

For a short operating manual for the latest camera and computer controls, read `CONTROL_GUIDE.md`.

## Read these three parts first

1. **What exists now:** the application, improved hand tracking, live and short-video training, testing, text, speech, a controlled reception agent, a persistent Staff desk, a focused competition-demo view, privacy-safe evidence export, participant deletion, an optional staff webhook and a separate computer-control experiment are built. A personalized ASL model trained only on Yusuf exists. No Emirati model exists yet.
2. **What must happen next:** fluent signers must validate the 8 sign forms, more real people must record examples, the Emirati model must be trained, the ASL model must be strengthened, and completely new people must test both models.
3. **What it is:** a bilingual prototype that recognizes one of 4 ASL signs or one of 4 Emirati signs during a short prompted recording. The SignBridge agent can turn confirmed results into predefined reception-desk requests, run safe local actions and remember a short session. It is not a full sign-language or sentence translator.

The difference between **software working** and **recognition working** is important. The software opens and the camera tracks correctly. Recognition cannot work until suitable human examples are recorded and the models are trained.

## 1. What the screenshot shows

The screenshot shows a healthy starting state:

- **Camera ready** means the webcam opened successfully.
- The coloured points and lines mean the dedicated MediaPipe hand tracker found a hand.
- The tracker follows up to two hands and smooths small jumps between frames.
- **Not trained yet** means the selected ASL classifier does not exist yet.
- **Sign forms reviewed: 0/4** means no fluent ASL signer has yet been recorded as approving the exact forms.
- **No prediction yet** is expected because no usable model exists.

That screenshot showed the earlier starting state. The project now contains a one-person ASL model, but it is still not validated for new people. The Emirati model is still untrained.

The tracking points are not sign recognition. MediaPipe is a pretrained tracker that finds locations such as wrists, fingers, shoulders and elbows. SignBridge still needs a second, locally trained model to learn which movement belongs to each supported sign.

## 2. The shortest explanation of the system

The complete path is:

```text
Webcam
  ↓
MediaPipe finds hands and upper-body points
  ↓
SignBridge records 1.8 seconds of movement
  ↓
The movement becomes a fixed sequence of numbers
  ↓
A language-specific model compares it with training examples
  ↓
Confidence and safety checks accept it or say “Not sure”
  ↓
Accepted result appears as English or Arabic text
  ↓
The user can approve it and play speech
```

All recognition runs locally on the computer after setup.

## 3. Why it was designed this way

### The starting idea

The inspiration video uses TensorFlow Object Detection to collect examples and recognize signs. Its useful idea is the workflow: collect examples, label them, train a model, then demonstrate it with a webcam.

SignBridge keeps that workflow but does not copy the older object-detection design. A sign is not simply an object inside a box. Its hand shape, location, direction and movement over time matter.

### The main design decisions

| Problem | Decision | Reason |
| --- | --- | --- |
| Only a laptop and webcam are available | Use normal RGB webcam video | No special gloves, depth camera or sensors are required |
| Signs contain movement | Record a short sequence, not one photograph | A still image loses direction and motion |
| Hands may move near the head or body | Track both hands and upper-body position | Hand shape alone is not always enough |
| The event deadline is short | Start with 8 isolated signs | A small system can be trained and tested honestly |
| ASL and Emirati Sign Language are different languages | Use separate vocabularies and separate models | A written meaning does not imply the same sign movement |
| Local data will be limited | Use a smaller classical classifier | A large LSTM or Transformer would be easier to overfit and harder to validate quickly |
| Wrong speech could mislead people | Reject uncertain results and make speech manual by default | Silence is safer than confidently saying the wrong word |
| Training accuracy can be misleading | Separate people by ID and add a final-test area | The model must be tested on people it never learned from |
| Public datasets have licence and dialect limits | Use local, consented landmark examples for version one | General Arabic data cannot prove an Emirati sign form |

### Why not build full sentence translation now?

Sign languages have their own grammar. Meaning can depend on two hands, movement, body position, facial expression and context. Joining individual word guesses does not create a correct sentence translator. Continuous translation needs much more data, specialist review and a different model.

## 4. What the system recognizes

The user chooses the active language. The two languages are never treated as direct translations of each other.

### ASL model with English output

- Hello
- Help
- Water
- Again

### Emirati Sign Language model with Arabic output

- يشرب — Drink
- يساعد — Help
- انتظار — Wait
- إعادة — Repeat

These are candidate forms linked to sign references. A fluent signer or qualified interpreter must still check the exact movement before training or public use.

## 5. What happens to one camera frame

The dedicated MediaPipe hand tracker handles the normal live preview. It uses a published hand model and tracking between frames, then SignBridge smooths the displayed points. This makes the hand skeleton feel steadier than running the larger whole-body model for every preview frame.

MediaPipe Holistic runs while a sign recording is active. SignBridge keeps a compact description rather than the image itself.

For classification, one frame contains **160 numerical values**:

- 7 useful upper-body points: nose, shoulders, elbows and wrists.
- 21 points for the left hand.
- 21 points for the right hand.
- Hand position relative to the body.
- A marker showing whether each hand was detected.

The hand points are measured relative to the wrist and palm size. The body points are measured relative to the shoulder centre and shoulder width. This normalization reduces the effect of a person being larger, smaller, nearer or farther from the camera.

The preview is flipped like a mirror because that feels natural to the user. Feature extraction happens consistently before that display flip.

MediaPipe may find face-related tracking points for its overall body solution, but this version does **not** feed facial grammar into the sign classifier.

## 6. What happens during one recording

1. The user presses a recording button.
2. A 2-second countdown gives the user time to prepare.
3. SignBridge records 1.8 seconds.
4. The number of webcam frames can vary, so the recording is converted to exactly 32 time steps.
5. SignBridge calculates both position and movement speed.
6. The final input contains 10,240 numbers: 32 time steps × 160 positions, plus 32 × 160 movement values.

For normal use and training, at least one hand must be visible during roughly 45% of the recording. Otherwise the sample is rejected and the user is asked to try again.

Final testing behaves differently: a poor attempt still counts. Silently discarding difficult final-test attempts would make the reported accuracy look better than the real system.

## 7. How the learning model works

There is one model for ASL and a separate model for Emirati Sign Language. Each model learns five classes: four supported signs plus **OTHER / NO SIGN**.

The training pipeline has three stages:

1. **Standardization:** puts different numerical features onto comparable scales.
2. **PCA compression:** reduces thousands of numbers to at most 48 useful patterns. This reduces noise and keeps training manageable.
3. **SVM classifier:** learns boundaries between the five classes. Probability calibration turns its scores into more useful confidence estimates.

An SVM was selected because this prototype uses a relatively small, structured landmark dataset and must train on an ordinary computer. A deep temporal model may become useful later with much more validated data, but it would not solve weak or incorrect training data.

### How a result is accepted

The model ranks every class. A result is accepted only when all three rules pass:

1. The best class is not `OTHER / NO SIGN`.
2. Its confidence is above the model threshold.
3. It beats the second-best choice by at least 12 percentage points.

The default confidence threshold is 82%. When there is enough multi-person training data, SignBridge searches for a threshold that aims for at least 95% correctness among accepted results while still accepting at least 60% of supported attempts.

A confidence score is not proof. It only describes how strongly this model prefers one choice based on the data it learned.

## 8. The six application screens

### SignBridge agent

This is the first screen and the main product demonstration. It completes a small, controlled communication-and-action loop instead of stopping at a sign label.

1. Choose ASL or Emirati Sign Language.
2. Press **Record a request sign** and perform one supported sign.
3. Read the camera suggestion and press **Yes, this sign is correct** or **No, try again**.
4. If the camera is unsure or wrong, use **Correction fallback** to select the intended supported sign manually. Manual selection still requires confirmation.
5. Choose the exact follow-up request. These choices are buttons; the camera did not translate a sentence.
6. Read the complete sentence and press **Confirm and show to staff**. Only this final confirmation allows speech and an action.
7. Read the **Agent action** card. Some requests create a local task number such as `SB-001`.
8. Staff can type a short reply for the signer to read.
9. Press **Continue with another sign** to keep the conversation in memory. `Again` or `Repeat` can then show the earlier staff reply.
10. Press **End and clear signer session**. The temporary conversation disappears and is not written to disk. The staff task remains until staff records its real outcome.

The first version uses a small rule-based action engine, not a chatbot. That makes every possible action visible, predictable and testable. Task numbers are saved locally and remain after a restart. They do not change bookings or summon an interpreter. A real staff notification happens only if an administrator explicitly configures and enables the optional webhook.

### Staff desk

This is the simple work queue for the person helping signers.

- New confirmed help requests appear as **Pending** tasks with IDs such as `SB-001`.
- Staff can **Accept**, type or choose a short reply, then **Complete** a task.
- Staff finishes with **Complete successfully**, **Mark wrong action** or **Cancel selected**. This prevents a wrong action from being counted as success.
- A reply also appears immediately in the open signer session when that session is still active.
- The summary shows pending, accepted, completed and delivered totals plus average completion time.
- Completed tasks are hidden by default but can be shown.
- Tasks are stored in `data/agent_tasks.json`; sign video is not stored there.
- The optional webhook can notify a Slack, Teams workflow or compatible HTTPS endpoint. It is off by default. Use **Send safe test** before enabling it for real tasks.
- A successful notification means only that the endpoint accepted the message. It does not prove a person read or completed it.
- **Export privacy-safe evidence report** produces aggregate completion, false-action, correction and timing measurements without replies or participant IDs.
- The privacy controls can forget the saved webhook URL or delete all local task history.

### Recognize

This is the demonstration screen.

- **Choose sign language:** selects the ASL or Emirati model.
- **Model status:** shows whether a model exists and whether multi-person testing was possible.
- **Supported signs:** shows the four possible results for the selected language.
- **Record one sign:** starts the countdown and 1.8-second recording.
- **Recognized sign:** displays accepted text and confidence.
- **Not sure:** means the safety checks rejected the prediction.
- **Two correction choices:** appear after an uncertain result. Choosing one is a user confirmation; it does not retrain the model.
- **Speak result:** speaks the currently approved result.
- **Automatic speech:** should remain off during testing. It can be enabled later for a controlled demonstration.
- **Undo and Clear:** change the on-screen history only.

The history is not a translated sentence. It is simply a list of accepted isolated results. It disappears when the application closes.

### Camera controls

- Camera **0** is the normal default webcam. Camera **1** and **2** mean other physical or virtual camera devices; they are not picture-quality levels.
- If the wrong camera opens or camera 0 is unavailable, choose **1** and press **Restart**. Try **2** only if needed.
- **Restart** safely closes the old camera connection before opening the selected one. It does not delete samples or models.
- The line below the preview shows the actual resolution, preview FPS, hand-tracking FPS and processing delay.
- The app requests a 1280×720 picture and uses smooth display scaling. MediaPipe receives a smaller copy, so a sharper preview does not multiply tracking cost.
- Small landmark jumps receive stronger smoothing while deliberate movement follows faster.
- If the line says **LOW CAMERA QUALITY**, Windows is giving the app less than 640×360. The app can enlarge it smoothly, but only an official driver update or a different webcam can add real detail.

### Train model

This is the data collection and model training screen.

- Select the language.
- Enter one stable Person ID, such as `trainer-01`.
- Select the sign to record.
- Open the exact reference link.
- Enter the fluent signer's or interpreter's name after review.
- Mark the selected form reviewed.
- Record training attempts live, or press **Import short video** for one consented 2–5 second clip containing exactly the selected sign.
- Use **Remove last sample** when the latest recording was clearly wrong. It is moved to a recoverable trash folder.
- Train or update the selected language model after enough data is collected.
- To honour a withdrawal, enter the participant's Person ID in the privacy section. Their training and final-test records are permanently deleted. Any trained model influenced by them is also removed and must be retrained.

The sample count shows a practical target of 30 for each class. Five examples per class is the technical minimum for checking whether the software pipeline can train, so you can start testing before reaching 30. A small dataset is not enough for a general accuracy claim.

Adding or removing samples does not change an existing model automatically. Press **Train or update** again.

### Final test

This screen measures the trained model on completely new people.

- Select the language.
- Enter a Tester ID, such as `final-01`.
- Select what the tester is expected to perform.
- Select the lighting or background condition.
- Record the attempt.
- The app records whether the model was correct, rejected the input or accepted the wrong result.

The app blocks a Person ID already found in training. It also blocks a final-test ID from later being added to training. This protection depends on honest, consistent IDs; the software cannot know that the same person used two different names.

Final-test records never become training data. Reports are tied to the exact model creation time. Retraining creates a new current-model report, while older raw attempts remain stored separately.

### Computer control

This is separate from sign-language recognition. It uses Google's generic hand-gesture model as a set of shortcuts.

1. Open **Computer control** and choose **Volume and slides** or **Mouse pointer and click**.
2. Press **Turn computer control on**.
3. Hold an open palm for 1.5 seconds to arm it.
4. Use the gestures listed on screen.
5. Press **Stop computer control** when finished.

For volume and slides, thumb up/down changes volume, victory moves to the next slide and pointing up moves to the previous slide. Release fully between commands; holding one gesture sends only one command.

For mouse mode, hold one index finger pointing up and move slowly. Lower it to pause and reposition your hand. The pointer moves relative to its current location instead of jumping to the hand's absolute camera position. Touching the thumb and index fingertip together clicks.

Control always starts off. Changing modes requires arming again. Leaving the tab, losing the camera or closing the app stops control. Seven-frame voting and action delays reduce accidental commands, but this remains an experiment and should be tested before a presentation.

### Resizing and navigation

- Drag any window edge or corner to resize the whole application.
- Use the normal Windows maximize button when preferred.
- Drag the divider between the camera and controls to give either side more space.
- Press **Full screen** or `F11` for full-screen mode.
- Press `Escape`, `F11` or **Exit full screen** to leave full-screen mode.
- Press **Reset layout** if the window or divider becomes awkward.
- Press **Competition demo** to hide training, testing, recognition-only and computer-control tabs. Press **Show setup tools** to restore them.
- Each controls page scrolls vertically when the window is too short to show every function at once.
- On a narrow controls panel, the tab names automatically shorten to **Agent**, **Use**, **Train**, **Test**, **Desk** and **PC**.

The camera preview expands with the available area while keeping the video proportions correct.

## 9. Correct setup and startup

In the current project folder:

1. Run `setup.ps1` once. This creates the private Python environment, installs the required software and downloads the official MediaPipe models if either is missing.
2. Double-click `Start SignBridge.vbs` whenever you want to use the app. It uses the windowed version of Python, so no PowerShell or terminal window remains open.

PowerShell is needed only for the one-time `setup.ps1` step. If the normal launcher fails, run `diagnose_signbridge.bat`; its terminal stays visible so you can read the error. Unexpected startup failures are also saved in `outputs/startup.log`.

The ZIP file is a package, not an executable application. Extract it first, run setup once, then use the launcher.

After setup, recognition runs locally. Internet is still needed to open external sign-reference links. Speech uses voices installed in Windows.

## 10. How to validate the sign forms

Do this before collecting a large dataset.

For each of the 8 signs:

1. Open its exact reference link from the training screen.
2. Ask a fluent signer or qualified interpreter for the relevant language to check it.
3. Confirm hand shape, palm direction, location, movement, two-handed coordination and any facial/body information.
4. Confirm that the variant is appropriate for the intended community.
5. Enter the reviewer's name and mark the form reviewed.

ASL review does not validate Emirati Sign Language, and general Arabic Sign Language does not automatically validate an Emirati variant.

The software records that a review was claimed; it cannot verify the reviewer's qualification.

## 11. How to collect training data properly

### People and volume

Thirty examples per class is a practical prototype target, not a magic accuracy number. The
number of different people matters more than repeating the same movement 30 times.
Only an untouched final test can show how well the model works.

Use the plan that is honest for the people available:

- **Personal event demo:** record 20 to 30 varied attempts per class from the
  person who will demonstrate it. This can be useful, but call it a personalized
  proof of concept. Do not claim that it works for everybody.
- **Better small demo:** use two or three training people with 10 to 15 attempts
  per class from each. Keep at least one different person completely untouched
  for Final test.
- **Unseen-person target:** use at least three training people with 10 attempts
  per class, then one or more completely different final testers. More people
  are still better when available.

If time is short, fewer well-tested signs are better than 8 weak signs.

Under the multi-person plans, each person should record:

- 10 attempts for each of the 4 supported signs.
- 10 to 20 varied `OTHER / NO SIGN` attempts.

That is 10 attempts per supported sign plus a varied OTHER / NO SIGN set.
Plan approximately 15 to 25 minutes per person once
instructions, selection changes and retries are included.

### Person IDs

- Ask for consent.
- Use a short code, not a full name.
- Keep the same ID for that person's entire session.
- Never use a training person in final testing.

Changing the ID for the same person makes the test logic believe they are different people and produces misleading results.

### Camera position

- Keep the face, shoulders, elbows and both hands inside the frame.
- Stand or sit far enough back for signs near the head and chest.
- Avoid strong light directly behind the person.
- Do not hide hands behind the body or outside the frame.
- Remove only accidental obstructions; normal clothing and realistic backgrounds should remain represented across the dataset.

### Performing each attempt

- Wait for the countdown.
- Perform exactly one sign during **Signing…**.
- Use the validated form, not a guess.
- Include the complete motion for a dynamic sign.
- For a held sign, keep the hand shape clear during the recording.
- Record natural variation instead of making every attempt mechanically identical.

### Good `OTHER / NO SIGN` examples

The unknown class prevents the model from forcing every movement into one of the four signs. Record varied unsupported movements with a hand visible, such as:

- A neutral hand position inside the frame.
- Waving when waving is not a supported class.
- Pointing.
- Adjusting clothing or glasses.
- Touching the face or hair.
- Other unsupported hand movements.
- Incomplete or deliberately unclear attempts.

Do not record only an empty frame. The model must learn that many visible hand movements are also unsupported.

### Variation that helps

Across the training people, vary:

- Body size and hand size.
- Distance from the camera.
- Plain and cluttered backgrounds.
- Normal, dim and brighter lighting.
- Clothing colours.
- Small natural differences in speed and position.

Do not create variation by teaching incorrect forms.

## 12. What happens when Train is pressed

1. SignBridge loads the stored examples for the selected language.
2. It checks that all four signs and the unknown class have at least five examples.
3. It warns if there are fewer than 20 examples per class, fewer than five people or unreviewed sign forms. You can still train a clearly labeled personalized model.
4. When at least three suitable people exist, it performs leave-one-person-out checks: it trains without one person and tests on that person, then repeats.
5. It calculates per-sign results, a balanced score and rejection behaviour.
6. It chooses a confidence threshold when the data supports that calculation.
7. It trains the final model using all training examples.
8. It saves the model and a readable metrics file.

The internal unseen-person score is helpful but is not the final event test. Those people still contributed to the overall development process. The **Final test** must use completely untouched people.

## 13. How to use the trained recognizer

1. Open **Recognize**.
2. Select ASL or Emirati Sign Language.
3. Check that the screen says a model is trained.
4. Frame the upper body and hands clearly.
5. Press **Record one sign**.
6. Prepare during the 2-second countdown.
7. Perform one complete sign during the 1.8-second recording.
8. Read the text and confidence.
9. If correct, press **Speak result**.
10. If the app says **Not sure**, retry or choose the intended correction if one of the displayed options is correct.

Do not repeatedly perform signs before pressing Record. This prototype only classifies the prompted recording window.

User corrections do not secretly train the model. New learning only occurs through the training screen followed by retraining.

### How to use the SignBridge agent

Use **SignBridge agent** for a short reception-desk interaction. An accepted camera prediction is only a suggestion. SignBridge remains silent and takes no action until the signer confirms the sign, chooses a follow-up request and confirms the complete sentence. A rejected prediction cannot advance the workflow or erase earlier conversation memory. Staff can reply, then the person can continue with another supported sign. Finish by clearing the session before the next person uses the app.

## 14. How to run the final test

Use at least two completely new people, preferably three.

For each language and each final tester:

1. Record every supported sign 10 times.
2. Record at least 20 unsupported movements.
3. Cover normal, dim, bright-background, cluttered-background and different-distance conditions.
4. Keep every attempt, including failures.

### Passing targets

- At least 85% balanced accuracy across the four supported signs.
- No individual sign below 75% recall.
- At least 95% of accepted results are correct.
- At least 95% of unsupported movements are rejected.
- No major condition loses more than 10 percentage points.
- The result appears within two seconds after capture finishes.

If one sign repeatedly fails, do not hide the result. Collect better validated data, replace that sign or reduce the event vocabulary.

### What the measurements mean

- **Per-sign recall:** out of all real attempts of one sign, how many were correctly accepted.
- **Balanced accuracy:** the average recall across all four signs, so an easy sign cannot hide a weak sign.
- **Accepted precision:** when the app decides to output something, how often it is correct.
- **Unknown rejection:** how often unsupported movements correctly produce no accepted sign.
- **Coverage:** how often valid supported attempts receive an accepted result rather than “Not sure.”
- **Model processing time:** classifier time only. It does not include the countdown or recording period.

## 15. Text and speech behaviour

Accepted predictions become English or Arabic text. Speech uses Qt's connection to the voices installed in Windows.

Speech is manual by default. This allows the user to check the text before the computer says it aloud. Automatic speech can be enabled only after accuracy is acceptable in a controlled demonstration.

Arabic text can appear even when Arabic speech is unavailable. If Windows has no compatible Arabic voice, the app reports that no voice is installed.

The system must not be presented as medical, emergency or accessibility equipment.

## 16. Data, privacy and stored files

The camera frames are processed in memory and shown in the preview. Live training does not save raw video. An imported clip is read once to extract landmarks and is not copied into the project.

It saves:

- Normalized hand and upper-body landmark sequences.
- A Person ID.
- Capture quality information.
- Validation records.
- Final-test outcomes.
- Trained model files and metrics.
- Local reception task type, status, delivery status and staff reply.
- Local webhook settings if an administrator saves them.

Landmarks are less revealing than video but should still be treated as potentially sensitive movement data. Person IDs are pseudonyms, not guaranteed anonymity. Ask for consent, protect the project folder and do not publish the data without permission.

## 17. Where everything is stored

| Location | Purpose |
| --- | --- |
| `app.py` | Starts the desktop application and records unexpected startup errors |
| `Start SignBridge.vbs` | Normal launcher; opens only the app with no terminal window |
| `diagnose_signbridge.bat` | Troubleshooting launcher that keeps technical errors visible |
| `signbridge/ui.py` | Builds the window and connects all buttons and workflows |
| `signbridge/camera.py` | Opens the webcam, runs MediaPipe and controls capture timing |
| `signbridge/computer_control.py` | Sends the explicitly enabled Windows volume, slide, pointer and click commands |
| `signbridge/landmarks.py` | Converts body and hand points into normalized model features |
| `signbridge/classifier.py` | Trains, evaluates, saves, loads and runs the classifiers |
| `signbridge/dataset.py` | Saves and loads training landmark samples |
| `signbridge/video_import.py` | Extracts landmarks from one short training clip without copying the raw video |
| `signbridge/tasks.py` | Saves and measures the local staff task queue |
| `signbridge/integrations.py` | Validates settings and sends optional staff webhook notifications |
| `signbridge/validation.py` | Stores fluent-signer review records |
| `signbridge/evaluation.py` | Stores final-test attempts and calculates reports |
| `signbridge/speech.py` | Produces local text-to-speech |
| `signbridge/config.py` | Contains timing, thresholds and important folders |
| `config/vocabulary.json` | Defines both language packs, text and source links |
| `assets/models/` | Contains the pretrained MediaPipe hand and Holistic tracking models |
| `data/samples/` | Contains local training landmark samples |
| `data/evaluations/` | Contains final-test attempts and reports |
| `data/validation.json` | Contains sign-form review records |
| `data/agent_tasks.json` | Contains local staff task status and replies; no video |
| `data/agent_settings.json` | Contains the optional webhook setting; protect this file because its URL may be secret |
| `models/` | Contains trained ASL and Emirati classifier files |
| `tests/` | Contains automated software tests |
| `docs/` | Contains research, collection, validation and testing guides |

Do not delete `data/` or `models/` after collecting and training unless you intentionally want to remove that work. Keep backups before the event.

## 18. What has been tested and what has not

### Software checks completed

- Landmark extraction has the expected size.
- Missing landmarks do not crash the feature pipeline.
- Training samples can be saved, loaded and recoverably removed.
- A synthetic classifier can train, save, load and predict.
- Final-test reports stay separated by model version.
- The vocabulary contains two separate four-sign packs.
- The desktop window loads with all six tabs.
- The SignBridge agent blocks speech and actions until the sign and complete request are confirmed.
- Every supported request maps to a tested action handler.
- Local tasks persist, can be accepted/replied to/completed and produce basic workflow measurements.
- Staff can label successful, wrong-action and cancelled outcomes instead of treating every closed task as success.
- The evidence report excludes replies, webhook URLs, camera data and participant identifiers.
- Participant deletion removes their training and final-test records and any affected trained model.
- Unsafe webhook URLs are rejected, and webhook payloads are tested without sending real requests.
- A short training video can be converted into the same 32-step landmark format without storing the raw video.
- A second turn can reuse an earlier staff reply.
- Rejected predictions cannot advance the guided session.
- Completing a guided session clears its temporary conversation.
- Both official MediaPipe models load successfully.
- Windows input commands are checked with a fake system interface during automated tests.
- The packaged copy loads and passes the same tests.
- The real launcher starts the application and initializes the camera pipeline.

### Still unproven

- Whether all 8 performed sign forms are correct.
- Real accuracy for any sign.
- Reliability across unseen people.
- Robustness at the event location.
- Arabic voice availability on another computer.
- Safety for accessibility, medical or emergency use.

Automated software tests cannot replace human language validation and real recognition tests.

## 19. Common problems

### “Camera ready” but Record does nothing

Read the model status. If it says **Not trained yet**, collect data and train that language first. Camera tracking and sign recognition are separate systems.

### The camera cannot open

Close Teams, Zoom, the Windows Camera app and every browser tab using the webcam,
then press **Restart**. A camera-testing website can keep the webcam busy even
when it is in the background. If camera 0 is still unavailable, try camera 1 or 2.

### The camera preview is slow or jerky

Read the FPS message at the top. If it says **Camera slow**, close browser and
meeting-camera tabs, add more light and restart SignBridge. Low light can make
some webcams expose each frame for longer. The preview and landmark tracker now
run separately, so slow tracking should not freeze an otherwise healthy preview.

### Hands were not clear

Move farther back, improve front lighting and keep at least one complete hand inside the frame during the recording.

### Results are often wrong

Do not lower the threshold first. Check sign correctness, collect more people, improve unknown examples, inspect weak signs and retrain.

### Results are usually “Not sure”

This can be safer than wrong output. Check framing and timing, then inspect training coverage and per-sign results. Only change thresholds after a proper final test.

### New samples did not improve recognition

The model does not update live. Press **Train or update this language model** again.

### Final-test statistics became empty after retraining

This is deliberate. A newly trained model needs a fresh untouched evaluation. Old attempts remain stored but are not counted as evidence for the new model.

### Arabic text works but speech does not

Install a compatible Arabic text-to-speech voice in Windows and restart the app.

### The ZIP does not start

Extract it, run `setup.ps1` once, then double-click `Start SignBridge.vbs`. If that fails, check `outputs/startup.log` or run `diagnose_signbridge.bat`.

## 20. A simple event explanation

Use this wording:

> SignBridge UAE is a local webcam prototype for recognizing 8 isolated signs: four ASL signs with English output and four Emirati signs with Arabic output. Its controlled reception agent asks the signer to confirm the result and complete request before speech or action. It creates a persistent staff task, supports a staff reply and can optionally notify one configured staff webhook. It does not make bookings or translate complete sign-language conversations.

### Suggested demonstration

1. State the limitation before demonstrating.
2. Open **SignBridge agent** and explicitly choose ASL or Emirati Sign Language.
3. Record one validated sign and show that SignBridge waits for confirmation.
4. Choose the exact request, confirm the sentence and let SignBridge speak it.
5. Open **Staff desk**, accept the task, type a staff reply and record the honest outcome.
6. Continue with an `Again` or `Repeat` turn, then end and clear the signer session.
7. Show an unsupported movement producing “Not sure” without advancing, speaking or acting.
8. Briefly show the Final test report and explain that new people were kept out of training.

Only quote an accuracy number produced by the untouched final-test process. Never quote training accuracy as product accuracy.

## 21. Questions people may ask

### Is it AI?

Yes. A pretrained vision model finds landmarks, and locally trained machine learning classifies the supported movements.

### Does it translate sign language?

No. It recognizes a limited set of isolated, prompted signs. The agent uses a confirmed sign to open predefined buttons; it does not convert free signing into sentences. Full translation is a larger future project.

### Why call it an agent?

It follows a controlled loop: observe a supported sign, ask for confirmation, choose an allowed function, run that function, remember the session, use a staff reply in a later turn and stop by clearing the task. The functions are local and deterministic in this version. It is not a general autonomous agent, and it deliberately does not use a chatbot yet.

### What actions can it perform now?

It can start a session, create persistent local tasks for directions, appointment help, interpreter help, general help or water help, show a waiting state, and recover an earlier staff reply after an `Again` or `Repeat` request. Staff can manage the queue inside SignBridge. An administrator may connect one tested staff-notification webhook. It still cannot change bookings or request an interpreter from an outside service.

### Does it work offline?

Recognition works locally after setup. External reference links need internet, and speech depends on installed Windows voices.

### Does it save video?

The current training workflow saves landmarks, not raw video. The video importer reads a selected clip once and does not copy it into SignBridge.

### Does it learn while someone uses it?

No. Learning happens only when training samples are recorded and the model is retrained.

### Why are there two models?

ASL and Emirati Sign Language are separate languages with independent sign forms.

### Why not use a large neural network?

The immediate dataset is small and the deadline is short. A smaller model is faster to train and easier to test. More complexity cannot repair bad labels or missing sign expertise.

### Can uploaded videos be supported?

Yes. **Train model → Import short video** accepts one short clip for one selected sign and saves its landmarks under that person's ID. It does not translate an arbitrary video or a sentence.

A remote participant should send separate 2-to-3-second clips, with their face,
shoulders, elbows and both hands visible. Keep the phone still, use good front
lighting, and name each clip with the language, sign and Person ID. Do not use that
person later as an untouched final tester.

### Can it work in online meetings?

Later, through local window capture, an overlay or a meeting-platform integration. Privacy, consent and platform-specific testing must come first.

## 22. What should happen next

Do these in order:

1. Find fluent ASL and Emirati Sign Language reviewers.
2. Validate all 8 forms before bulk recording.
3. Prepare stable training and final-tester ID lists.
4. Choose the honest data plan above. Reduce the sign list if the available data is too small.
5. Train both language models.
6. Run the full final test with two or three untouched people.
7. Test complete SignBridge agent tasks, including a second turn, and record false actions, corrections and completion time.
8. Remove, replace or postpone signs that miss the targets.
9. Ask Deaf or hard-of-hearing users and fluent signers to review whether the guided interaction is actually useful.
10. Back up `data/`, `models/` and the full project folder.

The software foundation is ready for that work. The current bottlenecks are correct human language data and feedback from the people the workflow is intended to help.
