# What comes after the event prototype

## Now: event prototype

- Webcam input.
- 4 isolated ASL signs and 4 isolated Emirati signs.
- The user chooses the language.
- One recorded attempt produces text, confidence and optional speech.
- Unsupported or unclear attempts should be rejected.

## Now: guided assistance upgrade

- One confirmed sign opens a small set of predefined reception-desk requests.
- The signer confirms both the sign and the complete request before speech.
- Staff can type a short reply.
- Completing the interaction clears its temporary conversation.
- Nothing is sent to an external service in this version.

The next proof is not a larger vocabulary. Test whether real users can finish the supported interaction without a false action, how often they need correction, and how long it takes.

This is the smallest version that can be trained and tested honestly before the event.

## Next: uploaded videos

This is possible. The same landmark and classifier pipeline can read frames from a video file instead of a webcam.

The first version should accept a short clip containing one of the same 8 signs. It must not claim to translate arbitrary videos or sentences. Add trimming, a progress indicator and a result timeline only after the webcam model passes its final test.

## Later: online meetings

This is also possible, but it is a separate integration project. Practical options are:

1. Capture a chosen meeting window locally and show SignBridge captions in its own small overlay.
2. Create platform-specific integrations that send approved text into meeting captions or chat.
3. Use a virtual camera only for displaying an overlay; it does not improve recognition.

Meeting capture needs clear consent, privacy controls and testing for each platform. Do not add it before the core recognizer is accurate.

## Long-term product

Continuous sign-language translation needs sentence-level training data, face and body information, grammar-aware models, qualified Deaf/sign-language experts and much larger testing. It cannot be created by joining isolated-word guesses together.
