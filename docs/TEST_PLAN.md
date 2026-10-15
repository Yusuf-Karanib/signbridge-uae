# Event test plan

The model passes only if all important checks pass.

## People

- Record only after the participant-consent box is checked.
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

## Agent and staff workflow

- Run at least 20 complete confirmed requests with target users.
- A wrong or rejected camera result must create zero tasks and zero notifications.
- Each confirmed help request must create exactly one task.
- Close and reopen the app; unfinished tasks must still appear in **Staff desk**.
- After staff marks a hotel service delivered, the guest must be asked whether it was resolved.
- A **resolved** answer must count as guest-confirmed success. **Still need help** must reopen the task instead of counting success.
- Verify that the visible agent progress matches task creation, notification, staff status and guest verification.
- Staff can accept and reply, then honestly mark each task delivered, wrong or cancelled without technical help.
- Record corrections, duplicate tasks, missed tasks and end-to-end completion time.
- If a webhook is enabled, test its safe test message first. Record every failed delivery and keep the local Staff desk as the fallback.
- A “Sent” webhook status means the endpoint accepted the message, not that a human read it.
- Export the privacy-safe evidence report and confirm that it contains no staff replies, webhook URL, video or participant identifiers.
- Separately record attempts that never created a task and time the full workflow from the first attempt. The current task export alone does not yet capture those measurements.

Suggested workflow target for the first pilot: at least 18 of 20 requests completed correctly, zero action from an unconfirmed sign, zero duplicate tasks and median completion under two minutes. These are prototype targets, not accessibility certification.

If these checks fail, reduce the vocabulary or replace confusing signs.

