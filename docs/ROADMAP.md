# What comes after the event prototype

## Current software foundation

- Webcam input.
- 4 candidate ASL signs and 4 candidate Emirati signs.
- The user chooses the language.
- One recorded attempt produces text, confidence and optional speech.
- Unsupported or unclear attempts should be rejected.

The software is not yet a validated bilingual recognizer. The local ASL model is personalized and has no unseen-person score; no Emirati model exists.

## Competition scope now

- Competition demo accepts only the `Help` sign.
- It offers only directions, appointment help and interpreter request.
- Interpreter request is the hero scenario.
- Best Societal AI Agent remains the recommended category.

## Current controlled reception workflow

- One confirmed sign opens a small set of predefined reception-desk requests.
- The signer confirms both the sign and the complete request before speech or action.
- A rule-based action engine creates persistent local reception tasks.
- The Staff desk can accept and reply to tasks, label successful/wrong/cancelled outcomes, export aggregate evidence and measure completion time.
- Staff can type a short reply, and the person can continue with another sign.
- The session remembers an earlier staff reply for `Again` or `Repeat`.
- Ending the signer interaction clears temporary conversation text. Staff independently records the persistent task's real outcome.
- An optional, administrator-configured HTTPS webhook can notify a real staff channel. It does not create bookings or request interpreters.

The next build is not a larger vocabulary. Add a visible goal-plan-tool-wait-verify-stop lifecycle, attempt-level evidence, visitor-confirmed outcomes and remote Final-test video import. Then test whether real users can finish the supported interaction without a false action.

## Now: first real service connection

- Choose one real setting, such as a reception desk.
- The app now supports one opt-in Slack/Teams-compatible staff notification webhook. A venue must provide and test its own URL.
- Booking, check-in and interpreter APIs are still future connections.
- Show the user exactly what will happen before every outside action.
- Record success, failure and cancellation without saving sign video.
- Keep a manual staff fallback whenever a service is unavailable.

This is the smallest version that can be trained and tested honestly before the event.

## Now: short training-video import

The Train model screen accepts a short clip containing exactly one selected sign. It extracts the same landmark sequence as live capture and does not copy the raw video. It does not translate arbitrary videos or sentences. Trimming, timelines and continuous-video translation remain future work.

## Later: online meetings

This is also possible, but it is a separate integration project. Practical options are:

1. Capture a chosen meeting window locally and show SignBridge captions in its own small overlay.
2. Create platform-specific integrations that send approved text into meeting captions or chat.
3. Use a virtual camera only for displaying an overlay; it does not improve recognition.

Meeting capture needs clear consent, privacy controls and testing for each platform. Do not add it before the core recognizer is accurate.

## Long-term product

Continuous sign-language translation needs sentence-level training data, face and body information, grammar-aware models, qualified Deaf/sign-language experts and much larger testing. It cannot be created by joining isolated-word guesses together.
