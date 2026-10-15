# SignBridge quick start

The full current control instructions are in `docs/CONTROL_GUIDE.md`.

1. Double-click `Start SignBridge.vbs` in the project folder. PowerShell is needed only for the first `setup.ps1` run.
2. Open **Train model**.
3. Open each exact source link and have a fluent signer check the form.
4. Confirm the participant-consent box. For a personalized demo, record 20 to 30 varied examples for every class from the demonstrator. A remote person can send separate 2–5 second clips; select the sign and Person ID, then use **Import short video**.
5. For stronger testing, use two or three training people with 10 to 15 examples per class from each.
6. Record varied `OTHER / NO SIGN` examples for every person.
7. Use a different Person ID for every person.
8. Train each language model.
9. Open **SignBridge agent**, choose the language and press **Record a request sign**.
10. Confirm the sign, choose the exact request and confirm the full sentence before speech.
11. Open **Staff desk**, accept the new task, save a reply and choose **Mark service delivered**, **Mark wrong action** or **Cancel selected** honestly.
12. Return to **SignBridge agent**. The guest confirms **resolved** or **still need help**. Only the guest's resolved confirmation counts as success.
13. A task is local unless an administrator configured and enabled the webhook. Even then, delivery does not prove a staff member read it.
14. Press **Continue with another sign** to keep the conversation memory, or **End and clear signer session** when finished. Ending the signer session does not silently mark the staff task successful.
15. Use **Final test** with at least one completely new person; two or three is better.
16. Press **Competition demo** for the focused guest-and-staff hotel presentation. This mode allows only `Help`, then check-in assistance, room/hotel service or interpreter request. Export the aggregate evidence report from **Staff desk** after real trials.

The clean sharing ZIP intentionally contains no participant data or personal trained model. On another computer, run setup and train or import consented landmark samples before expecting camera recognition.

For computer control, open **Computer control**, choose a mode, turn it on and hold an open palm for 1.5 seconds. Leave that tab or press **Stop** to disable it. These are generic shortcuts, not ASL or Emirati signs.

The simple **Recognize** screen keeps speech manual by default. The SignBridge agent always requires confirmation of the sign and full request before speech or action.

Before the event, get every sign you keep checked by fluent signers. Thirty recordings from one person do not prove unseen-person accuracy.

This prototype is built for isolated signs, but its current camera models are not yet validated on unseen people. It does not translate full conversations.

If the window does not open, run `diagnose_signbridge.bat` and read the visible error, or open `outputs/startup.log`.

