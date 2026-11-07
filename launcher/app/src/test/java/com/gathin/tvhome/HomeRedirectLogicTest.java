package com.gathin.tvhome;

import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

import org.junit.Test;

public class HomeRedirectLogicTest {
    private static final String OWN = "com.gathin.tvhome";
    private static final String HOME_CLASS = "com.amazon.tv.launcher.ui.HomeActivity_vNext";

    @Test
    public void amazonHomeIsRedirectedUntilSettingsLatchesTheGate() {
        HomeRedirectLogic.Gate gate = new HomeRedirectLogic.Gate();
        assertTrue(gate.onWindow("com.amazon.tv.launcher", HOME_CLASS, OWN));
        assertFalse(gate.onWindow("com.amazon.tv.launcher", "com.amazon.tv.launcher.ui.OtherActivity", OWN));
        assertFalse(gate.onWindow("com.example.app", HOME_CLASS, OWN));
        assertFalse(gate.onWindow(null, HOME_CLASS, OWN));
    }

    @Test
    public void settingsFailsClosedWithNoTimerUntilTheLauncherIsOpenedAgain() {
        HomeRedirectLogic.Gate gate = new HomeRedirectLogic.Gate();
        assertFalse(gate.onWindow("com.amazon.tv.settings.v2", "x.Y", OWN));
        assertTrue(gate.inSettings());
        // the home flash, however late it comes, and other windows in between, stay unredirected
        assertFalse(gate.onWindow("com.amazon.tv.launcher", HOME_CLASS, OWN));
        assertFalse(gate.onWindow("com.example.app", "x.Y", OWN));
        assertFalse(gate.onWindow("com.amazon.tv.launcher", HOME_CLASS, OWN));
        // the user opens this launcher: resumed
        assertFalse(gate.onWindow(OWN, "com.gathin.tvhome.MainActivity", OWN));
        assertFalse(gate.inSettings());
        assertTrue(gate.onWindow("com.amazon.tv.launcher", HOME_CLASS, OWN));
        // quick settings latch it too
        assertFalse(gate.onWindow("com.amazon.tv.quicksettings", "x.Y", OWN));
        assertFalse(gate.onWindow("com.amazon.tv.launcher", HOME_CLASS, OWN));
    }
}
