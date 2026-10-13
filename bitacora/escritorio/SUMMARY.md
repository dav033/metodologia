# escritorio — Summary

_Rewritten (not appended) whenever the state changes. Keep it under ~60 lines._

## Purpose
_What this project is and who it is for._
Last confirmed with owner: YYYY-MM-DD (set only after the owner confirms; otherwise write `not yet confirmed`).

## Current state
Personal Arch/Hyprland desktop configuration. Super+B opens a wallpaper selector with direct-to-trash removal, rotation pause/resume, and 15/30/60/120-minute choices. After deleting, the selector keeps its list position for continued cleanup. New images still apply automatically. Super alone opens the Super+Space launcher; Print and Super+Shift+S save screenshots in `~/images/Screenshots` and copy them to the clipboard. Alt+1/Alt+2 are registered for next/previous Firefox tabs when Firefox is focused. A custom grave-key image-saving extension and secure local receiver are prepared. AMO accepted version 1.0.0 as a self-distributed add-on (0 validation errors, 1 warning); the version is awaiting review and signing. The signed XPI and manual installation in personal Firefox remain pending.

The Super launcher has an Energy tab for existing profiles, screen controls, configurable idle timeout, and scheduled suspension. Its former left illustration is now a profile/CPU/RAM/root-disk/NVIDIA/Intel status dashboard sampled when the launcher opens. Rofi uses opaque dark surfaces, brighter secondary text, a stronger selection highlight, and larger type so controls remain legible over light wallpapers.

## Active focus
- P-002: Download the signed Firefox image saver after AMO review, then install it manually.

## Top pending (see PENDING.md)
- P-001: Spot-check Alt+1/Alt+2 in Firefox during normal use.
- P-002: Download the signed custom grave-key image-saving extension after AMO review, then install it manually.

## Recent decisions (see DECISIONS.md)
- Energy controls reuse the existing profile and headless-panel wrappers; the left Rofi panel shows an escaped hardware snapshot on open.
- Wallpaper deletion is immediate but recoverable through desktop trash; scheduled rotation defaults to enabled/30 minutes, with current live preference paused/30 minutes.
- Firefox stable requires Mozilla signing for permanent installation; the extension obtains its receiver token through an ID-restricted native messaging host instead of embedding the secret in its package.

## Known issues
- The focused Firefox Alt+1/Alt+2 behavior is implemented and loaded, but its final tab-switch effect was not verified in an isolated test window.

_Last updated: 2026-10-12_
