# script.irblaster.service
Kodi service addon to support low-latency raw IR blasting to arbitrary devices

## Background
I have a media center setup that looks roughly like the following:


                                    ┌────┐
                                    │ TV │
                                    └─▲──┘
                                      │
                                     HDMI
                                      │
         ┌──────┐               ┌─────┴─────┐           ┌────────────┐
         │ Kodi ├────HDMI───────┤ Denon AVR ├───HDMI────┤ Android TV │
         └──┬───┘               └─────▲─────┘           └────────────┘
            │                         │
           USB                        │
            │                         │
      ┌─────┴──────┐                  │
      │   MCEUSB   │                  │
      │Recv/Blaster├───Blaster─Cable──┘
      └────────────┘

The MCE remote setup has worked well for me for many years, going through many different
XBMC/Kodi-based systems. The big win with Microsoft's MCE remote was that it had the
ability to indepently reprogram the volume and TV power buttons on the remote directly.
That way, the device I plugged the MCEUSB receiver into didn't need to know how to
adjust the volume or turn my TV on/off.

However, the Wife Acceptance Factor (WAF) has recently caused me to hide the Denon AVR
in a cabinet which causes it not to receive the IR signals from my MCE remote. This
problem forced me to consider using the IR blasting capabilities of the MCEUSB receiver
to control the volume of my Denon AVR.

It was fairly easy to determine how to emulate the button presses of any arbitrary
device using `ir-ctl`, and at first, I mapped button presses for certain MCE remote
buttons via Kodi's keymap XMLs. However, this presented a new problem: high latency.

You see, the ability to customize the keymap of Kodi inputs is somewhat limited. You
can either trigger Kodi's built-in list of actions, or use RunScript to execute an
external script file. As you might guess, executing an external script involves 
forking and running that external script as a new process, which is what is responsible
for this additional latency.

Additionally, if Kodi was busy with other tasks, it added even more latency to this
process, meaning that doing something like holding down a volume key on the remote
would be a very bad experience, as it wouldn't adjust the volume smoothly. It would be
a bit jumpy on a mostly-idle Kodi system, and significantly delayed on a busy one.

## The Solution

I decided that I needed a process which could stay running in the background, so that
the system wasn't wasting time forking processes each time a button was pressed.
`ir-ctl` wasn't designed with this use-case in mind, so I decided to try to implement
the minimal amount of functionality that I needed in my own application. I also
decided that running as a Kodi service would be ideal for integration with Kodi itself.

On OpenElec/LibreElec/CoreElec systems, inputs are all received by a process called
[eventlircd] (https://github.com/OpenELEC/eventlircd). The key presses are communicated
to Kodi via a Unix domain socket. This provided a way for me to intercept the key-press
data in real-time (or as real-time as Kodi receives them, anyway), as I could simply 
connect to the same Unix domain socket, and listen for incoming key press events, and
then execute my own IR blasting routines without having to fork to a new process.

So then, the solution looks like the following:


      ┌──────────┐       ┌────────────┐       ┌────────────┐
      │ IR Input ├──────►│ eventlircd ├──────►│Unix Socket │
      └──────────┘       └────────────┘       └┬─────────┬─┘
                                               │         │
                                               │         │
                                               │         │
                   ┌──────────────────┐        │   ┌─────▼─┐
                   │ script.irblaster │◄───────┘   │ Kodi  │
                   └────────┬─────────┘            └───────┘
                            │
                          Blast
                            │
                      ┌─────▼─────┐
                      │ Denon AVR │
                      └───────────┘

It should be noted that you'll want to add "noop" handlers into your kodi keymap in order
to prevent Kodi from acting on the inputs that you want mapped to script.irblaster.

## Project Status

This project should be considered only to be at a proof-of-concept stage.

As of now, I have the solution working for my own system, handling volume up/down, and
changing of inputs on the AVR. There is some hard-coded data in the current project (
such as the actual data blasted to the Denon AVR), so the code as it is won't be as
useful to other people. However, the bones of this solution is what's important to other
people: low-latency IR blasting from within Kodi.

I will entertain pull requests which adds support for generically configuring key codes
and blasted data.
