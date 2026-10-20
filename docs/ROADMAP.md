# What comes after the event prototype

For the startup-programme route covering Hub71 Initiate, Access, Hub71+ AI,
the DCAI government accelerator and Hub71 Sandbox, read
[`STARTUP_PROGRAMME_ROADMAP.md`](STARTUP_PROGRAMME_ROADMAP.md). The short answer
is to prepare for Initiate first and leave the other programmes until SignBridge
has real users, customer evidence and deployment readiness.

## Current software foundation

- Webcam input.
- 4 active candidate ASL signs with English output.
- Emirati vocabulary remains saved but hidden until after ASL feedback.
- One recorded attempt produces text, confidence and optional speech.
- Unsupported or unclear attempts should be rejected.

The software is not yet a validated ASL recognizer. The local ASL model is personalized and has no unseen-person score.

## Competition scope now

- Competition demo accepts only the `Help` sign.
- It offers only hotel check-in assistance, room/hotel service help and interpreter request.
- Interpreter request is the hero scenario.
- Best Societal AI Agent remains the recommended category.

## Current controlled hotel workflow

- One confirmed sign opens a small set of predefined hotel-service requests.
- The signer confirms both the sign and the complete request before speech or action.
- A rule-based action engine creates persistent local hotel-staff tasks.
- The Staff desk can accept and reply to tasks, mark service delivered, label wrong/cancelled actions, export aggregate evidence and measure completion time.
- The guest confirms whether the delivered service actually resolved the request; only that confirmation counts as success.
- The agent panel visibly shows goal confirmation, task creation, notification, staff progress, guest verification and session clearing.
- Staff can type a short reply, and the person can continue with another sign.
- The session remembers an earlier staff reply for `Again`.
- Ending the signer interaction clears temporary conversation text. Staff independently records the persistent task's real outcome.
- An optional, administrator-configured HTTPS webhook can notify a real staff channel. It does not create bookings or request interpreters.

The next build is not a larger vocabulary. Add attempt-level evidence, complete workflow timing and remote Final-test video import. Then test whether real users can finish the supported hotel interaction without a false action.

## Now: first real service connection

- Use a hotel reception as the first concrete setting.
- The app now supports one opt-in Slack/Teams-compatible staff notification webhook. A venue must provide and test its own URL.
- Reservation, identity, room-key, payment and interpreter APIs are still future connections.
- Show the user exactly what will happen before every outside action.
- Record success, failure and cancellation without saving sign video.
- Keep a manual staff fallback whenever a service is unavailable.

This is the smallest version that can be trained and tested honestly before the event.

## Now: ASL training-video import

The Train model screen accepts a short clip containing exactly one selected sign. It also accepts one official PopSign `game/train` sign folder for `Hello`, `Help` or `Water`, limited to 30 varied signers' clips per import. It extracts the same landmark sequence as live capture and does not copy raw video into SignBridge. It does not translate arbitrary videos or sentences. `Again`, negative examples, final-test video import and continuous translation remain separate work.

## Later: online meetings

This is also possible, but it is a separate integration project. Practical options are:

1. Capture a chosen meeting window locally and show SignBridge captions in its own small overlay.
2. Create platform-specific integrations that send approved text into meeting captions or chat.
3. Use a virtual camera only for displaying an overlay; it does not improve recognition.

Meeting capture needs clear consent, privacy controls and testing for each platform. Do not add it before the core recognizer is accurate.

## Long-term product

Continuous sign-language translation needs sentence-level training data, face and body information, grammar-aware models, qualified Deaf/sign-language experts and much larger testing. It cannot be created by joining isolated-word guesses together.

After the ASL model receives credible unseen-person and target-user feedback, restart Emirati development with fluent Emirati signers and properly licensed UAE data. Do not transfer ASL movements or model weights as if the languages were interchangeable.
