# SignBridge UAE build status

## Built and tested

- Responsive two-hand preview using Google's dedicated MediaPipe hand tracker.
- Camera 0/1/2 selection, safe restart and visible preview/hand-tracking FPS.
- 4 ASL signs and 4 Emirati Sign Language signs.
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

A real webcam capture previously produced the expected 32-step landmark sequence. The new hand model was also tested on the supplied gesture-control video and found hands in 105 of 120 sampled frames. The preview runs separately from sign capture so the larger body model does not slow normal viewing. Automated tests pass. Recheck the live FPS message after closing every browser or meeting tab that uses the webcam.

## Still required before the event

1. Have fluent signers check the exact sign forms linked inside the app.
2. Choose either a clearly labeled personalized demo or a multi-person training plan.
3. Record 20 to 30 varied attempts per class for a personalized demo, or 10 to 15 per class from each of two or three training people.
4. Train both language models.
5. Test at least one new person who was not used for training; two or three is better.
6. Keep only signs that pass the test plan.

The sign recognizer is not pre-trained yet because it needs real, correctly performed examples. It is an 8-sign isolated-sign prototype, not a full sign-language translator. The generic control gestures use Google's separate pretrained model and must not be described as sign-language translation.
