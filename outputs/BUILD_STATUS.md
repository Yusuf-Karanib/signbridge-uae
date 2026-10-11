# SignBridge UAE build status

## Built and tested

- Responsive two-hand preview using Google's dedicated MediaPipe hand tracker.
- Camera 0/1/2 selection, safe restart and visible preview/hand-tracking FPS.
- 4 ASL signs and 4 Emirati Sign Language signs.
- A Guided Assistance workflow that turns a confirmed sign into one predefined reception-desk request.
- Separate confirmation of the detected sign and complete request before any guided speech.
- A manual correction fallback, typed staff replies and temporary session clearing.
- Optional Windows computer control for volume, slides, pointer and click.
- Computer control starts off, requires a 1.5-second open-palm hold and stops when its tab is left.
- Separate training model for each language.
- English and Arabic on-screen text and offline Windows speech.
- Confidence score, “not sure” rejection, two correction choices, undo and clear.
- Manual speech by default, with optional automatic speech for a controlled demo.
- `OTHER / NO SIGN` training examples to reduce false detections.
- Local landmark storage; raw camera video is not saved.
- Unseen-person accuracy report when at least three people have recorded every class.
- A separate **Final test** area that blocks training people and keeps results out of training.
- Reports for accuracy, false acceptance, unknown rejection, test conditions and model processing time.

A real webcam capture previously produced the expected 32-step landmark sequence. The new hand model was also tested on the supplied gesture-control video and found hands in 105 of 120 sampled frames. The preview runs separately from sign capture so the larger body model does not slow normal viewing. All 31 automated tests pass, including confirmation safety, temporary session clearing and the resizable layout. A startup/shutdown check passed on 12 October 2026, but camera 0 was busy or unavailable during that check. Recheck the live camera after closing every browser, meeting or Camera app that may use it.

## Still required before an accuracy or accessibility claim

1. Have fluent signers check the exact sign forms linked inside the app.
2. Choose either a clearly labeled personalized demo or a multi-person training plan.
3. Record 20 to 30 varied attempts per class for a personalized demo, or 10 to 15 per class from each of two or three training people.
4. Train both language models.
5. Test at least one new person who was not used for training; two or three is better.
6. Keep only signs that pass the test plan.
7. Test the complete Guided Assistance task with target users and measure corrections, false actions and completion time.

A personalized ASL model trained only on Yusuf exists. It has not been validated on unseen people, and its **Help** and **OTHER / NO SIGN** classes have much less data than the other classes. No Emirati model exists yet. This remains an 8-sign isolated-sign prototype, not a full sign-language translator. The generic control gestures use Google's separate pretrained model and must not be described as sign-language translation.
