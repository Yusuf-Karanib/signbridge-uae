# Create AI Agents Championship guide

## Rechecked verdict — 14 October 2026

Keep the project, category and narrow reception-desk problem. Do not present the current build as a validated bilingual MVP yet.

- Recommended category: **Best Societal AI Agent**.
- Working name: **SignBridge Desk Assistant**.
- Honest current stage: **Prototyping**.
- Hero outcome: request a human sign-language interpreter.
- Secondary outcomes: ask for directions or appointment help.
- The competition demo now exposes only the `Help` sign and those three goals.

Official pages checked on 14 October 2026:

- https://www.dubaichamberdigital.com/en/create-ai-agents
- https://www.dubaichamberdigital.com/en/create-ai-agents-register-your-interest

Registration of interest was confirmed on 13 October. The confirmation says the Howspace area opens on 19 October. The main timeline says registration and submission are in January 2027, while the FAQ and launch announcement say registration closes in December 2026. Copy the exact portal deadline when access arrives and treat that as controlling.

The current terms say entry is open globally, teams may have up to six people, submission materials are in English, and a winner must establish or already have a Dubai company to receive the grant.

## Important eligibility question

The overview allows a new AI-agent capability from an existing project, while the terms also say the submitted agent has not been used before. SignBridge's earlier detector was publicly demonstrated and the repository is public; the Desk Assistant capability was added after the competition launched.

Ask the organizer in writing whether adapting this non-commercial detector into the new Desk Assistant agent is eligible. Keep the answer. Do not hide the earlier prototype or claim it was never shown.

## What genuinely exists now

- A working desktop application and camera pipeline.
- Eight configured candidate signs: four ASL and four Emirati Sign Language signs.
- Confidence rejection and confirmation before any action.
- Persistent staff tasks, replies, outcomes and an optional webhook.
- Aggregate evidence export and local deletion controls.
- Fifty automated tests pass after the review fixes.

Recognition is not ready for a competition claim:

- The saved ASL model uses one training person and has no unseen-person result.
- Its weakest classes need more data and retesting.
- No trained Emirati model exists.
- No final-test attempts exist yet.
- The clean sharing package intentionally excludes personal training data and trained models, so it requires setup and training.

## Smallest strong product

A Deaf or hard-of-hearing visitor uses one externally validated `Help` sign, confirms the result, then chooses one supported service goal. SignBridge safely completes the desk workflow instead of pretending to translate a full language.

The competition story must show this full agent loop:

1. Understand the visitor's confirmed goal.
2. Build a bounded plan from approved steps.
3. Use the local staff queue and, when configured, the notification tool.
4. Wait for staff acceptance or a safe failure.
5. Return the staff reply to the visitor.
6. Ask whether the problem was solved, record the honest outcome and stop.

The current build handles the queue and reply, but its planning is still mostly fixed routing. A visible goal/plan/tool/status trace is the next necessary product feature. An LLM is not required.

## Evidence required

- Recognition results from completely unseen people.
- Supported-sign accuracy and unsupported-gesture rejection.
- Every rejected attempt and manual correction, including attempts that create no task.
- Zero action from an unconfirmed sign.
- Visitor-confirmed task completion and false-action rate.
- Time from the first attempt to the final outcome, plus staff handling time.
- At least 20 complete desk trials.
- Feedback from Deaf or UAE sign-language users, not only hearing developers.

The current task report covers created tasks and staff completion time. Attempt-level evidence, visitor confirmation and full-workflow timing still need to be added.

## Privacy rules

- Live and imported video is not retained by default.
- Training now requires an explicit consent confirmation and stores that fact with the landmark sample.
- Raw landmark samples, staff replies and webhook settings remain local data and are not automatically safe merely because they are local.
- The exported aggregate report excludes replies, URLs, video and participant IDs.
- Before a venue pilot, define who can open the app and how long local records are retained.

## Exact priority

1. On 19 October, enter Howspace, record the real deadline and ask the prior-prototype eligibility question.
2. Build the visible goal-plan-tool-wait-verify-stop lifecycle.
3. Add attempt-level evidence, visitor outcome confirmation and full-workflow timing.
4. Add short-video import to **Final test** so remote unseen users can participate without their clips entering training.
5. Obtain fluent-signer and Deaf-user validation.
6. Train and pass unseen-person tests for one language first. Treat Emirati as the UAE priority; add ASL to the pitch only if it also passes.
7. Test one real staff endpoint and run 20 complete desk trials.
8. Only then produce the summary report, pitch deck and demo video.

## Do not build or claim now

- No continuous sign-language translation.
- No emergency or medical reliability.
- No universal “Arabic Sign Language” claim.
- No larger vocabulary, chatbot, meeting integration, arbitrary-video translation or computer control in the competition pitch.
- No accuracy claim based on Yusuf or training data.
- No “check-in completed” claim; the current action creates appointment help only.
