# SignBridge UAE build status

Review began 25 October; final verification completed 26 October 2026. See `docs/REVIEW_2026_10_25.md`.

## Software built and tested

- Responsive two-hand preview using Google's dedicated MediaPipe hand tracker.
- Camera 0/1/2 selection, safe restart and visible preview/hand-tracking FPS.
- 4 active ASL signs with English text and speech. Emirati work is saved but deferred.
- A controlled hotel access agent that turns a confirmed sign into one predefined request and safe local action.
- Separate confirmation of the detected sign and complete request before any agent action or guided speech.
- Local task IDs for hotel check-in assistance, room/hotel service, interpreter requests and the broader prototype's legacy help actions.
- A persistent Staff desk where tasks can be accepted, replied to and marked delivered after an app restart.
- Guest verification that records resolved requests or reopens requests that still need help.
- Honest task outcomes: guest-confirmed success, wrong action or cancelled.
- Aggregate task-completion, guest-resolution, false-action, correction and staff-completion-time evidence with privacy-safe JSON export.
- A visible agent progress trail from confirmed goal through staff handling, guest verification and session clearing.
- A one-click **Competition demo** view that shows only the guest agent and Staff desk and limits the flow to `Help` plus three hotel-service goals.
- An optional HTTPS Slack/Teams-compatible staff notification webhook, disabled until explicitly configured.
- Basic task totals, delivery failures and average completion-time measurement.
- Short-session memory, including showing an earlier staff reply after the ASL `Again` request.
- A manual correction fallback, typed staff replies, another-sign continuation and temporary session clearing.
- Optional Windows computer control for volume, slides, pointer and click.
- Computer control starts off, requires a 1.5-second open-palm hold and stops when its tab is left.
- ASL training model with English on-screen text and offline Windows speech.
- Confidence score, “not sure” rejection, two correction choices, undo and clear.
- Manual speech by default, with optional automatic speech for a controlled demo.
- `OTHER / NO SIGN` training examples to reduce false detections.
- Local landmark storage; raw camera video is not saved.
- Explicit consent confirmation for new live or imported training samples, stored in sample metadata.
- Short training-video import for remote participants; the selected raw video is not copied into SignBridge.
- Guarded PopSign ASL v2.1 folder import for up to 30 original `game/train` clips of Hello, Help or Water, with licence metadata, duplicate blocking and train/test separation.
- Permanent Person ID deletion across readable landmark samples and final-test records; all trained models are removed for safe retraining, and unreadable files are reported.
- Controls to forget the webhook secret and delete all local service-task history.
- Unseen-person accuracy report when at least three people have recorded every class.
- A separate **Final test** area that blocks training people and keeps results out of training.
- Final-test video import with permission confirmation, exact-file duplicate/split checks and separate live/video counts. It saves no test video or test landmarks.
- Calibration transforms fitted inside each calibration split; development checks are clearly separated from independent final testing.
- The same low-visibility rejection in real use and Final test, plus recorded capture failures.
- Service journeys that include rejected input, manual fallback, abandonment before task creation and full first-attempt-to-guest-resolution timing.
- Transactional task saves, recovery from empty/stalled capture, and safe waiting for workers during shutdown.
- Reports for accuracy, false acceptance, unknown rejection, test conditions and model processing time.

A real webcam capture previously produced the expected 32-step landmark sequence. The hand model was also tested on the supplied gesture-control video and found hands in 105 of 120 sampled frames. Those are historical hardware checks. The 25 October review passes 88 automated tests covering the updated calibration, final-video import, visibility rejection, exact-file split checks, service-journey timing, persistence failures, worker shutdown and compact layout, alongside the earlier functionality. Test and Staff-desk screens were rendered with Windows fonts, including a 960 × 640 layout check. The physical webcam was not opened during this review. Existing sharing ZIPs were not rebuilt.

## Still required before an accuracy or accessibility claim

1. Have fluent signers check the exact sign forms linked inside the app.
2. Choose either a clearly labeled personalized demo or a multi-person training plan.
3. Record 20 to 30 varied attempts per class for a personalized demo, or 10 to 15 per class from each of two or three training people.
4. Train the ASL model.
5. Test at least one new person who was not used for training; two or three is better.
6. Keep only signs that pass the test plan.
7. Test complete SignBridge hotel tasks with target users and measure corrections, false actions, guest-confirmed resolution and completion time.

An older personalized ASL model trained only on Yusuf exists. Retrain it once to use the corrected calibration; the file and saved samples have been retained. The checked sample counts are Hello 32, Help 7, Water 33, Again 31 and OTHER / NO SIGN 5, all from one person. No real Final-test attempts, service tasks or service journeys exist yet. The current model has no unseen-user evidence and must not support an accuracy claim. Sharing packages intentionally exclude personal samples, source dataset videos and trained models. The policy engine remains bounded fixed routing rather than open-ended reasoning. A hotel can configure a notification webhook, but no reservation, room-key, payment or interpreter system is connected.
