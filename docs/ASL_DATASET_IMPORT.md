# Import different ASL signers safely

## What this is for

The PopSign importer helps the ASL model learn from more than one person without asking every person to stand beside this computer.

It accepts original clips from Georgia Tech's **PopSign ASL v2.1** dataset. The dataset is published under **CC BY 4.0**, contains 47 signers and is meant for isolated-sign recognition. It is not evidence that SignBridge can translate full signed conversations.

Official source: https://signdata.cc.gatech.edu/view/datasets/popsign_v2_1/index.html

Official download guide: https://signdata.cc.gatech.edu/view/guides/downloading_popsign/index.html

## Signs that match the current app

- `Hello`
- `Help`
- `Water`

PopSign does not list `Again`. Do not use `Another` or another word as a replacement. `Again` and `OTHER / NO SIGN` still need their own correct examples.

## Download only the original TRAIN clips

Use the official `game/train` archives. Do not train from the small website preview videos: PopSign says those previews are heavily resized and their speed is changed.

- Hello: https://signdata.cc.gatech.edu/data/popsign_v2_1/game/train/hello.tar
- Help: https://signdata.cc.gatech.edu/data/popsign_v2_1/game/train/help.tar
- Water: https://signdata.cc.gatech.edu/data/popsign_v2_1/game/train/water.tar

Keep the folders clearly named like this:

```text
PopSign/
  game/
    train/
      hello/
      help/
      water/
```

Extract each archive into its matching sign folder. Keep `val` and `test` separate; the app deliberately refuses to add them to training.

## Import into SignBridge

1. Open **Train model**.
2. Press **Import a PopSign training folder**.
3. Choose one folder, such as `PopSign/game/train/help`.
4. Read the summary and press **Yes**.
5. Wait for the import to finish.
6. Repeat for `hello` and `water` if needed.
7. Add correct `Again` and varied `OTHER / NO SIGN` examples separately.
8. Retrain the ASL model.

Each import is limited to 30 clips and is ordered to prefer different signers. Duplicate clips are skipped. SignBridge saves extracted landmarks and attribution details, not another copy of the raw video.

The downloaded videos still exist in the folder where you extracted them. SignBridge does not delete those source files.

## What still counts as a real test

Training on different people is useful, but it is not the final score. Use **Final test** with people or properly licensed test clips that were never used during training. Enter the expected sign and consistent Tester ID, confirm testing permission, then choose **Import test video**.

The app saves the result and exact-file fingerprint, not the video or its landmarks. It blocks training people, exact clips used for training and repeated clips within one model's final report. The PopSign importer also checks final-test fingerprints. Re-encoded copies and one person under two different IDs still need human review; file checking is not automatic identity recognition.

Only one sign per clip is supported. This feature does not translate conversations. Keep development experiments separate from the untouched final evidence used in a pitch.
