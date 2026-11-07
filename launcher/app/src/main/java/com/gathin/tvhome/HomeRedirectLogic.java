package com.gathin.tvhome;

/**
 * The decisions of HomeRedirectService, with no Android classes in them so a plain JUnit test can run them
 * (docs/fireos.md). The accessibility-list edit lives in tools/home_redirect.py.
 */
final class HomeRedirectLogic {
    private HomeRedirectLogic() {}

    static final String AMAZON_LAUNCHER = "com.amazon.tv.launcher";
    static final String AMAZON_HOME = "HomeActivity";
    static final String[] SETTINGS_PACKAGES = {"com.amazon.tv.settings", "com.amazon.tv.quicksettings"};

    // ---- when to open the launcher -------------------------------------------------------------------------

    /**
     * Fail closed around Amazon Settings. Amazon's Home flashes up on the way into Settings; instead of guessing
     * with a timer, a window of Amazon's settings app latches the gate and nothing is redirected until this
     * launcher's own window shows again (the user opened it from the apps row).
     * Leaving Settings therefore lands on Amazon's Home and stays there until the user chooses to resume.
     */
    static final class Gate {
        private boolean inSettings;

        boolean inSettings() {
            return inSettings;
        }

        /** True when this window change should open the launcher over Amazon's Home. */
        boolean onWindow(String pkg, String cls, String ownPackage) {
            if (pkg == null || cls == null) return false;
            for (String settings : SETTINGS_PACKAGES) {
                if (pkg.startsWith(settings)) {
                    inSettings = true;
                    return false;
                }
            }
            if (pkg.equals(ownPackage)) {
                inSettings = false;
                return false;
            }
            return !inSettings && pkg.equals(AMAZON_LAUNCHER) && cls.contains(AMAZON_HOME);
        }
    }
}
