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
9. Open **Recognize**, choose the language and press **Record one sign**.
10. Use **Final test** with at least one completely new person; two or three is better.

For computer control, open **Computer control**, choose a mode, turn it on and hold an open palm for 1.5 seconds. Leave that tab or press **Stop** to disable it. These are generic shortcuts, not ASL or Emirati signs.

Speech is manual by default. Check the text, then press **Speak result**. Automatic speech is optional for a controlled demo.

Before the event, get every sign you keep checked by fluent signers. Thirty recordings from one person do not prove unseen-person accuracy.

This prototype recognizes isolated signs. It does not translate full conversations.

If the window does not open, run `diagnose_signbridge.bat` and read the visible error, or open `outputs/startup.log`.

