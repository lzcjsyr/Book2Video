# Motion Principles

## Layout Before Animation

Position every element where it should be at its most visible moment before
adding animation. Use `gsap.from()` to animate from hidden/offscreen states into
the CSS-defined final layout.

## Timing

- Use `durationSeconds` as the total composition duration.
- Reserve the last 0.25-0.5 seconds for a stable hold or clean exit.
- Stagger related elements by 0.1-0.2 seconds.
- Avoid all elements entering simultaneously.

## Safety

- Text must not overflow the frame.
- Avoid negative letter spacing.
- Do not rely on viewport units for core text size.
