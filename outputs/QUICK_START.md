# SignBridge quick start

The full current control instructions are in `docs/CONTROL_GUIDE.md`.

1. Double-click `Start SignBridge.vbs` in the project folder. PowerShell is needed only for the first `setup.ps1` run.
2. Open **Train model**.
3. Open each exact source link and have a fluent signer check the form.
4. For a personalized demo, record 20 to 30 varied examples for every class from the demonstrator.
5. For stronger testing, use two or three training people with 10 to 15 examples per class from each.
6. Record varied `OTHER / NO SIGN` examples for every person.
7. Use a different Person ID for every person.
8. Train each language model.
9. Open **SignBridge agent**, choose the language and press **Record a request sign**.
10. Confirm the sign, choose the exact request and confirm the full sentence before speech.
11. Read the agent action. A local task number does not mean an outside service was contacted.
12. Let staff type a reply. Press **Continue with another sign** to keep the conversation memory, or **Complete task and clear session** when finished.
13. Use **Final test** with at least one completely new person; two or three is better.

For computer control, open **Computer control**, choose a mode, turn it on and hold an open palm for 1.5 seconds. Leave that tab or press **Stop** to disable it. These are generic shortcuts, not ASL or Emirati signs.

The simple **Recognize** screen keeps speech manual by default. The SignBridge agent always requires confirmation of the sign and full request before speech or action.

Before the event, get every sign you keep checked by fluent signers. Thirty recordings from one person do not prove unseen-person accuracy.

This prototype recognizes isolated signs. It does not translate full conversations.

If the window does not open, run `diagnose_signbridge.bat` and read the visible error, or open `outputs/startup.log`.

