# SignBridge current-version control guide

This is the short guide for operating the version used at the summit.

## 1. Start the app

Double-click `Start SignBridge.vbs`. PowerShell is needed only for the one-time setup.

## 2. Choose the camera

The numbers select camera devices. They are not quality settings.

- **0 — default camera:** normally the built-in laptop webcam. Use this first.
- **1 — second camera:** another USB, virtual or phone camera, if installed.
- **2 — third camera:** a third installed camera, if one exists.

On this laptop, the check on 5 October found:

- **0:** Integrated Camera.
- **1:** OBS Virtual Camera. It is normally black unless OBS is open and configured.
- **2:** no camera was found.

Therefore, use **0** for the built-in camera. Choosing 1 or 2 cannot improve camera 0's quality.

If the picture is correct, leave it on 0. If it is black, unavailable or shows the wrong camera, try 1 and press **Restart**. Then try 2 only if needed. Changing the number does not delete training data.

The status below the picture shows the actual resolution and speed. The new version requests 1280×720, but the webcam may choose a lower resolution if that is all it supports.

### Important result from this laptop

The built-in Realtek camera currently offers desktop apps only **160×120 at 10 FPS**. That is why the enlarged image looks soft or pixelated. SignBridge now enlarges the raw picture more smoothly and draws the hand lines after enlarging, so the overlay is cleaner. It cannot invent missing image detail.

The installed camera driver is from 24 March 2020. Before the summit, the safe options are:

1. Open **Windows Update > Advanced options > Optional updates** and install an official Lenovo/Realtek camera update if one is offered.
2. Alternatively, use **Lenovo Support** for the exact **Lenovo Legion 5 15IMH05H (model 81Y6)**. Do not use a random driver-download website.
3. If no official update is available, use a normal USB webcam. This is the most dependable quick fix.

Restart Windows after a driver update, then open SignBridge. A successful fix will make the status show at least 640×360 instead of 160×120.

## 3. Get a clean camera result

- Put light in front of you, not behind you.
- Keep the camera still.
- Keep the complete hand inside the frame.
- Stay roughly an arm's length from the camera.
- Close browser, Teams, Zoom and Camera windows that may also use the webcam.
- Move clearly rather than extremely quickly.

## 4. Recognize a sign

The **Recognize**, **Train model** and **Final test** tabs are for the 8-sign language prototype. Choose ASL or Emirati Sign Language, press the recording button, wait for the countdown and perform one sign while the bar fills.

This is separate from computer control.

## 5. Turn computer control on

The control gestures are generic shortcuts. They are not ASL or Emirati signs.

1. Open **Computer control**.
2. Choose a mode.
3. Press **Turn computer control on**.
4. Hold an open palm until the status says **ARMED**.
5. Press **Stop computer control** when finished.

Leaving the Computer control tab also stops it.

## 6. Volume and slides mode

| Gesture | Action |
| --- | --- |
| Thumb up | Volume up one step |
| Thumb down | Volume down one step |
| Victory / two fingers | Next slide |
| One index finger pointing up | Previous slide |

Hold the gesture until the screen says **steady**. Each hold sends only one command. Fully release or change the gesture before giving the next command.

For PowerPoint, start the slideshow first and leave it as the active window. SignBridge can remain behind it while the camera continues running.

## 7. Mouse mode

1. Arm control with an open palm.
2. Raise one index finger. The first detection anchors to the pointer's current position, so it should not jump across the screen.
3. Move the pointing finger slowly to move the pointer.
4. Lower the finger to pause. Reposition your hand, then point again to continue.
5. While pointing, touch the thumb and index fingertip together once to click.

Open palms and random hand movement do not move the pointer. Movement is relative, slowed and limited per frame.

## 8. If control feels unstable

Press **Stop computer control** first. Then:

- Use one hand for control.
- Move farther from the camera if the hand fills most of the picture.
- Improve front lighting.
- Keep the palm facing the camera for the safety hold.
- Make one clear gesture, hold it, then release it fully.
- Use **Volume and slides** for the summit if mouse mode is still uncomfortable. It is safer and easier to demonstrate.

The revised mouse mode no longer maps one hand position directly to the whole screen. Pointing starts from the pointer's current position, tiny movements are ignored, large steps are limited, and lowering the index finger pauses movement. This reduces jumping, but the 160×120 camera feed can still limit accuracy.

## 9. If the camera shows coloured static

The older version used a low-latency buffer setting that this Realtek camera cannot handle. That setting has been removed. The current version also ignores obvious rainbow-noise frames and reconnects automatically up to three times.

If coloured static remains, close every SignBridge, Camera, Zoom, Teams and browser camera window. Open SignBridge once and use camera 0. Press **Restart** once only if needed.

