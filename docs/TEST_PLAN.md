# Event test plan

The model passes only if all important checks pass.

## People

- Test with at least two people, preferably three, whose recordings were not used for training.
- Each person performs every sign ten times.
- Each person also performs at least twenty unsupported gestures or resting movements.
- Use the **Final test** tab. It rejects any Person ID already present in training.

## Accuracy

- At least 85% balanced accuracy across the four signs in each language.
- No sign below 75% recall.
- At least 95% of accepted results should be correct.
- Reject at least 95% of unsupported gestures.

## Conditions

- Normal indoor lighting.
- Dim lighting.
- A moderately bright background.
- Plain and cluttered backgrounds.
- Different distances from the camera.

Accuracy should not fall by more than 10 percentage points between conditions.

## Experience

- Result appears within two seconds after capture.
- One capture creates one output only.
- Low-confidence attempts do not speak.
- Confident attempts appear as text first; automatic speech is optional.
- Undo, clear and correction choices work.
- English and Arabic speech work without event Wi-Fi.

If these checks fail, reduce the vocabulary or replace confusing signs.

