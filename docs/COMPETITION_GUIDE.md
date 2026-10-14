# Create AI Agents Championship guide

## Current application status

- Registration of interest was confirmed on 13 October 2026.
- The confirmation says the Howspace learning and community area opens on 19 October 2026.
- The full submission deadline must be copied from the portal when access arrives because the public pages have shown conflicting months.
- Recommended category: **Best Societal AI Agent**.
- Competition name: **SignBridge Desk Assistant**.

## Smallest strong product

SignBridge Desk Assistant helps a Deaf or hard-of-hearing visitor complete a limited service-desk request when an interpreter is not immediately available.

The competition demonstration should focus on three supported outcomes:

1. Ask for directions.
2. Ask for appointment or check-in help.
3. Ask staff for a human sign-language interpreter.

The agent observes a supported isolated sign, rejects uncertainty, asks the visitor to confirm or correct it, chooses an allowed request, creates and optionally notifies a staff task, waits for staff, records the outcome and clears the temporary signer session. It is deterministic by design; an LLM is not required to make it an agent.

## How to demonstrate it

1. Start SignBridge and press **Competition demo**.
2. Choose the supported language mode.
3. Perform a supported sign or use the clearly labelled manual fallback.
4. Show that no action happens before sign and request confirmation.
5. Confirm one of the three target desk requests.
6. Open **Staff desk**, accept it, reply and choose **Complete successfully**.
7. End and clear the signer session. The task outcome remains as evidence.
8. Show one uncertain or wrong attempt creating no task.
9. Export the privacy-safe evidence report.

## Evidence the app now records

- Total tasks created.
- Successful, wrong-action and cancelled outcomes.
- Task-completion rate.
- False-action rate among outcomes where the chosen action was judged correct or wrong. Cancelled requests do not hide mistakes.
- Manual correction/fallback rate.
- Average and median staff completion time.
- Webhook delivery successes and failures.
- Task counts by action, language and input method.

Staff must label outcomes honestly. The exported JSON report excludes staff replies, webhook URLs, camera data and participant IDs.

## Privacy controls

- Live and imported video is not retained by default.
- Training requires a Person ID and consent.
- **Train model** can permanently delete one Person ID from training and final-test records.
- If a deleted person influenced a trained model, that model is removed and must be retrained.
- **Staff desk** can forget the saved webhook URL and permanently clear local task history.
- Ending the signer session clears temporary conversation text but does not silently mark the staff task successful.

## Do not add or claim yet

- No continuous sign-language translation.
- No emergency or medical reliability.
- No universal “Arabic Sign Language” claim; use only validated UAE/Emirati forms.
- No larger vocabulary until the current forms pass unseen-user testing.
- No chatbot, online-meeting integration or computer-control feature in the competition pitch.
- No accuracy claim based only on Yusuf or training data.

## Human work still required

1. Fluent signers must validate every retained sign form.
2. Deaf/UAE sign-language users must review whether the workflow is useful.
3. Completely unseen people must perform the final recognition test.
4. Run at least 20 full desk-task trials and label every outcome.
5. Configure a venue-controlled webhook only when a real test endpoint is available.
6. Prepare the required summary report, pitch deck and demo video after the portal reveals its exact fields.
