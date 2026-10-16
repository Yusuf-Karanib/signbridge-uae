# Data collection

Keep this simple and consistent.

Current phase: collect and test ASL only. Emirati work is paused until the ASL workflow receives useful feedback.

1. Ask the participant for permission before recording.
2. Give them a Person ID. Do not use their full name.
3. Show the validated reference sign.
4. Record live, or use **Import short video** for one 2–5 second consented clip containing exactly the selected sign. Use the same Person ID either way.
5. For a personalized demo, collect 20 to 30 varied examples of every class from the demonstrator.
6. If possible, use two or three training people with 10 to 15 examples per class from each.
7. Each person also provides 10 to 20 `OTHER / NO SIGN` examples: resting, waving, adjusting clothing and unsupported gestures.
8. Change distance, background and lighting during the session.
9. For the current 30-example target, aim for three ASL training people with 10 examples per sign. More people are better when available.
10. Keep at least one different person for final testing; two or three is better. Record them only in the **Final test** tab so they can never enter training accidentally.

For extra ASL training variety, the separate PopSign importer may use original CC BY 4.0 `game/train` folders for `Hello`, `Help` and `Water`. It derives anonymous participant IDs from the published filenames and limits each import to 30 clips. It does not cover `Again` or `OTHER / NO SIGN`, and it refuses PopSign validation/test folders. See `ASL_DATASET_IMPORT.md`.

Five samples per class is only the technical minimum for checking that the pipeline works. It is not enough for an event accuracy claim.

Thirty examples is not a guarantee. Thirty attempts from one person still do not prove that the model works for a new person.

The app stores extracted landmark coordinates. It does not save live video or copy an imported video. Keep the sender's original clip somewhere appropriate only if they consented to that separate storage.

