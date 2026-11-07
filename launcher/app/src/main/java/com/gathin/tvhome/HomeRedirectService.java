package com.gathin.tvhome;

import android.accessibilityservice.AccessibilityService;
import android.content.Intent;
import android.view.accessibility.AccessibilityEvent;

/**
 * Opens this launcher over Amazon's Home on Fire OS, which ignores the default-home setting. Concept from
 * itsmeterrylin/fire-tv-cleanup (ab4d9bf), reworked: see docs/fireos.md.
 *
 * OFF by default: nothing enables it at install. It runs only while the person has put it on the accessibility
 * list (Settings > Accessibility, or tools/home_redirect.py enable --confirm). It never disables Amazon's
 * launcher, and Amazon Settings fail closed (HomeRedirectLogic.Gate). It does nothing at boot.
 */
public class HomeRedirectService extends AccessibilityService {
    private final HomeRedirectLogic.Gate gate = new HomeRedirectLogic.Gate();

    @Override
    public void onAccessibilityEvent(AccessibilityEvent event) {
        if (event.getEventType() != AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED) return;
        CharSequence pkg = event.getPackageName(), cls = event.getClassName();
        if (gate.onWindow(pkg == null ? null : pkg.toString(), cls == null ? null : cls.toString(), getPackageName()))
            startActivity(new Intent(this, MainActivity.class)
                    .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_NO_ANIMATION));
    }

    @Override
    public void onInterrupt() {
    }
}
