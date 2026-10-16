# Create AI Agents Championship guide

## Rechecked verdict — 15 October 2026

Keep the project and category, but focus the competition demo on an ASL hotel-reception workflow where no accessible self-service option is assumed. Do not present the current build as a validated translator.

- Recommended category: **Best Societal AI Agent**.
- Working name: **SignBridge Access Agent — Hotel Pilot**.
- Honest current stage: **Prototyping**.
- Hero outcome: request a human sign-language interpreter.
- Secondary outcomes: ask for hotel check-in assistance or room/hotel service help.
- The competition demo now exposes only the `Help` sign and those three goals.

Official pages checked on 14 October 2026:

- https://www.dubaichamberdigital.com/en/create-ai-agents
- https://www.dubaichamberdigital.com/en/create-ai-agents-register-your-interest

Registration of interest was confirmed on 13 October. The confirmation says the Howspace area opens on 19 October. The main timeline says registration and submission are in January 2027, while the FAQ and launch announcement say registration closes in December 2026. Copy the exact portal deadline when access arrives and treat that as controlling.

The current terms say entry is open globally, teams may have up to six people, submission materials are in English, and a winner must establish or already have a Dubai company to receive the grant.

## Important eligibility question

The overview allows a new AI-agent capability from an existing project, while the terms also say the submitted agent has not been used before. SignBridge's earlier detector was demonstrated at AI Everything and the repository is public, but Yusuf says it was never deployed, sold or used operationally. The Access Agent capability was added after the competition launched.

Ask the organizer in writing whether adapting this non-commercial detector into the new Access Agent is eligible. Keep the answer. Do not hide the earlier prototype or claim it was never shown.

## What genuinely exists now

- A working desktop application and camera pipeline.
- Four active ASL candidates with English output. The Emirati configuration is saved but deferred.
- Confidence rejection and confirmation before any action.
- Persistent hotel-staff tasks, replies, guest-confirmed outcomes and an optional webhook.
- A visible goal, task, notification, staff, guest-verification and session-clear progress trail.
- Aggregate evidence export and local deletion controls.
- Sixty automated tests pass, including the ASL-only scope and guarded PopSign training-folder importer.

Recognition is not ready for a competition claim:

- The saved ASL model uses one training person and has no unseen-person result.
- Its weakest classes need more data and retesting.
- No final-test attempts exist yet.
- The clean sharing package intentionally excludes personal training data and trained models, so it requires setup and training.

## Smallest strong product

A Deaf or hard-of-hearing hotel guest uses one externally validated `Help` sign, confirms the result, then chooses one supported hotel-service goal. SignBridge coordinates the task instead of pretending to translate a full language.

The competition story must show this full agent loop:

1. Understand the visitor's confirmed goal.
2. Build a bounded plan from approved steps.
3. Use the local staff queue and, when configured, the notification tool.
4. Wait for staff acceptance or a safe failure.
5. Return the staff reply to the visitor.
6. Ask whether the problem was solved, record the honest outcome and stop.

The current build now shows this fixed, bounded lifecycle and records the guest's final answer. It remains deterministic routing rather than open-ended reasoning; an LLM is not required.

## Evidence required

- Recognition results from completely unseen people.
- Supported-sign accuracy and unsupported-gesture rejection.
- Every rejected attempt and manual correction, including attempts that create no task.
- Zero action from an unconfirmed sign.
- Visitor-confirmed task completion and false-action rate.
- Time from the first attempt to the final outcome, plus staff handling time.
- At least 20 complete hotel-service trials.
- Feedback from Deaf or UAE sign-language users, not only hearing developers.

The current task report covers created tasks, staff completion time and guest-confirmed outcomes. Attempt-level evidence and full first-attempt-to-outcome timing still need to be added.

## Privacy rules

- Live and imported video is not retained by default.
- Training now requires an explicit consent confirmation and stores that fact with the landmark sample.
- Raw landmark samples, staff replies and webhook settings remain local data and are not automatically safe merely because they are local.
- The exported aggregate report excludes replies, URLs, video and participant IDs.
- Before a venue pilot, define who can open the app and how long local records are retained.

## Exact priority

1. On 19 October, enter Howspace, record the real deadline and ask the prior-prototype eligibility question.
2. Add attempt-level evidence and full-workflow timing.
3. Add short-video import to **Final test** so remote unseen users can participate without their clips entering training.
4. Obtain fluent-signer and Deaf-user validation.
5. Improve and pass unseen-person ASL tests first. Restart Emirati work only after useful ASL feedback and access to fluent Emirati reviewers.
6. Test one real hotel-staff endpoint and run 20 complete hotel-service trials.
7. Only then produce the summary report, pitch deck and demo video.

## Do not build or claim now

- No continuous sign-language translation.
- No emergency or medical reliability.
- No universal “Arabic Sign Language” claim.
- No larger vocabulary, chatbot, meeting integration, arbitrary-video translation or computer control in the competition pitch.
- No accuracy claim based on Yusuf or training data.
- No “check-in completed” claim; the current action creates a hotel check-in assistance task and does not contact reservations, identity checks or room-key systems.
