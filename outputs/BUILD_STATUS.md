# SignBridge UAE build status

## Software built and tested

- Responsive two-hand preview using Google's dedicated MediaPipe hand tracker.
- Camera 0/1/2 selection, safe restart and visible preview/hand-tracking FPS.
- 4 ASL signs and 4 Emirati Sign Language signs.
- A controlled reception agent that turns a confirmed sign into one predefined request and safe local action.
- Separate confirmation of the detected sign and complete request before any agent action or guided speech.
- Local reception task IDs for directions, appointments, interpreter requests, general help and water help.
- A persistent Staff desk where tasks can be accepted, replied to and completed after an app restart.
- Honest task outcomes: successful, wrong action or cancelled.
- Aggregate task-completion, false-action, correction and staff-completion-time evidence with privacy-safe JSON export.
- A one-click **Competition demo** view that shows only the visitor agent and Staff desk and limits the flow to `Help` plus three competition goals.
- An optional HTTPS Slack/Teams-compatible staff notification webhook, disabled until explicitly configured.
- Basic task totals, delivery failures and average completion-time measurement.
- Short-session memory, including showing an earlier staff reply after the `Again` or `Repeat` request.
- A manual correction fallback, typed staff replies, another-sign continuation and temporary session clearing.
- Optional Windows computer control for volume, slides, pointer and click.
- Computer control starts off, requires a 1.5-second open-palm hold and stops when its tab is left.
- Separate training model for each language.
- English and Arabic on-screen text and offline Windows speech.
- Confidence score, “not sure” rejection, two correction choices, undo and clear.
- Manual speech by default, with optional automatic speech for a controlled demo.
- `OTHER / NO SIGN` training examples to reduce false detections.
- Local landmark storage; raw camera video is not saved.
- Explicit consent confirmation for new live or imported training samples, stored in sample metadata.
- Short training-video import for remote participants; the selected raw video is not copied into SignBridge.
- Permanent Person ID deletion across readable landmark samples and final-test records; all trained models are removed for safe retraining, and unreadable files are reported.
- Controls to forget the webhook secret and delete all local reception history.
- Unseen-person accuracy report when at least three people have recorded every class.
- A separate **Final test** area that blocks training people and keeps results out of training.
- Reports for accuracy, false acceptance, unknown rejection, test conditions and model processing time.

A real webcam capture previously produced the expected 32-step landmark sequence. The hand model was also tested on the supplied gesture-control video and found hands in 105 of 120 sampled frames. The preview runs separately from sign capture so the larger body model does not slow normal viewing. All 50 automated tests pass, covering confirmation safety, task outcomes, evidence privacy, participant deletion, webhook safety, imported-video extraction, negative examples, conversation memory, computer control and the focused/resizable layout. A startup/shutdown check passed on 14 October 2026. Recheck the live camera after closing every browser, meeting or Camera app that may use it.

## Still required before an accuracy or accessibility claim

1. Have fluent signers check the exact sign forms linked inside the app.
2. Choose either a clearly labeled personalized demo or a multi-person training plan.
3. Record 20 to 30 varied attempts per class for a personalized demo, or 10 to 15 per class from each of two or three training people.
4. Train both language models.
5. Test at least one new person who was not used for training; two or three is better.
6. Keep only signs that pass the test plan.
7. Test complete SignBridge agent tasks with target users and measure corrections, false actions and completion time.

A personalized ASL model trained only on Yusuf exists. It has not been validated on unseen people, and its **Help** and **OTHER / NO SIGN** classes have much less data than the other classes. A replay over its own stored samples rejected most attempts, so it should be treated as unreliable until it is retrained and tested live. No Emirati model exists yet and no Final-test attempts exist. The clean sharing ZIP intentionally excludes personal samples and trained models. Local agent tasks persist, but the current policy engine is fixed routing rather than a strong visible plan. A venue can configure a notification webhook, but no booking or interpreter system is connected. This is a prototype, not a validated bilingual product or full sign-language translator.
